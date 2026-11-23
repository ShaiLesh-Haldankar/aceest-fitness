#!/usr/bin/env bash
# Installs kubectl + minikube (if missing) into ~/bin and starts a single-node cluster using the Docker driver.
set -euo pipefail
mkdir -p "$HOME/bin"; export PATH="$HOME/bin:$PATH"
if ! command -v kubectl >/dev/null; then
  curl -sSL -o "$HOME/bin/kubectl" "https://dl.k8s.io/release/$(curl -sSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
  chmod +x "$HOME/bin/kubectl"
fi
if ! command -v minikube >/dev/null; then
  curl -sSL -o "$HOME/bin/minikube" https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
  chmod +x "$HOME/bin/minikube"
fi
grep -q 'HOME/bin' "$HOME/.bashrc" || echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
minikube start --driver=docker --cpus=2 --memory=3072
kubectl get nodes
echo "Cluster IP: $(minikube ip)"
