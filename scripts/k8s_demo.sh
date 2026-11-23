#!/usr/bin/env bash
# Demonstrates all five deployment strategies plus rollback on the running Minikube cluster and prints evidence.
# Usage: DOCKERHUB_USER=<user> bash scripts/k8s_demo.sh | tee k8s-demo-output.txt
set -uo pipefail
export PATH="$HOME/bin:$PATH"
: "${DOCKERHUB_USER:?set DOCKERHUB_USER}"
IP=$(minikube ip)
IMG="docker.io/$DOCKERHUB_USER/aceest-fitness"
hdr() { echo; echo "=================== $* ==================="; }
ver() { curl -s --max-time 5 "$@" | grep -o '"version":"[0-9.]*"' || echo "(no answer)"; }

hdr "Cluster"; kubectl get nodes; echo "Endpoint base: http://$IP"
hdr "Deploy all manifests"; kubectl apply -f k8s/
for d in aceest-rolling aceest-blue aceest-green aceest-canary-stable aceest-canary-new aceest-shadow-prod aceest-shadow-new aceest-shadow-gw aceest-ab-a aceest-ab-b aceest-ab-gw; do
  kubectl rollout status deployment/$d --timeout=180s >/dev/null && echo "ready: $d"
done
kubectl get pods,svc -o wide | grep -v kubernetes

hdr "1. ROLLING UPDATE (zero downtime) :30081"
echo -n "before: "; ver http://$IP:30081/health
kubectl set image deployment/aceest-rolling app=$IMG:1.2.0
kubectl rollout status deployment/aceest-rolling --timeout=120s
echo -n "after update: "; ver http://$IP:30081/health
kubectl rollout history deployment/aceest-rolling
echo "--- rollback (kubectl rollout undo)"
kubectl rollout undo deployment/aceest-rolling; kubectl rollout status deployment/aceest-rolling --timeout=120s
echo -n "after rollback: "; ver http://$IP:30081/health

hdr "2. BLUE-GREEN :30082"
echo -n "live = blue : "; ver http://$IP:30082/health
echo "--- switch traffic to green"; kubectl patch service aceest-bg -p '{"spec":{"selector":{"app":"aceest-bg","version":"green"}}}'
echo -n "live = green: "; ver http://$IP:30082/health
echo -n "new endpoint /api/stats on green -> HTTP "; curl -s -o /dev/null -w "%{http_code}\n" http://$IP:30082/api/stats
echo "--- instant rollback to blue"; kubectl patch service aceest-bg -p '{"spec":{"selector":{"app":"aceest-bg","version":"blue"}}}'
echo -n "live = blue : "; ver http://$IP:30082/health

hdr "3. CANARY (3 stable : 1 canary) :30083"
echo "20 requests -> version distribution:"
for i in $(seq 1 20); do ver http://$IP:30083/health; done | sort | uniq -c
echo "--- rollback canary: scale canary to 0"; kubectl scale deployment/aceest-canary-new --replicas=0; sleep 5
echo "20 requests after rollback:"; for i in $(seq 1 20); do ver http://$IP:30083/health; done | sort | uniq -c
kubectl scale deployment/aceest-canary-new --replicas=1 >/dev/null

hdr "4. SHADOW (mirror to 1.2.0, responses discarded) :30084"
echo -n "client sees: "; ver http://$IP:30084/health
curl -s -X POST http://$IP:30084/api/clients -H 'Content-Type: application/json' -d '{"name":"ShadowTest","height":170,"weight":65,"program":"BG"}'; echo
curl -s http://$IP:30084/api/stats; echo "(404 from prod 1.0.1: stats exists only in 1.2.0)"
sleep 2
echo "--- shadow pod (1.2.0) logs show the mirrored requests:"; kubectl logs deployment/aceest-shadow-new --tail=6
echo "--- prod pod (1.0.1) logs:"; kubectl logs deployment/aceest-shadow-prod --tail=3

hdr "5. A/B TESTING (route by header) :30085"
echo -n "no header   -> A: "; ver http://$IP:30085/health
echo -n "X-Variant: B -> B: "; ver -H 'X-Variant: B' http://$IP:30085/health

hdr "6. AUTOMATIC ROLLBACK on a bad release"
bash scripts/deploy_with_rollback.sh aceest-rolling $IMG:9.9.9 40
echo -n "service still healthy on: "; ver http://$IP:30081/health
hdr "Done"
