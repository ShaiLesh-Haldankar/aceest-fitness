#!/usr/bin/env bash
# Waits for the SonarQube analysis, writes sonar-report.txt and fails the build if the quality gate is not OK.
set -euo pipefail
HOST="${SONAR_HOST:-http://localhost:9000}"
KEY="${SONAR_PROJECT_KEY:-aceest-fitness}"
AUTH="${SONAR_TOKEN}:"
CE_URL=$(grep '^ceTaskUrl=' .scannerwork/report-task.txt | cut -d= -f2-)
STATUS=""
for _ in $(seq 1 40); do
  curl -s -u "$AUTH" "$CE_URL" > .scannerwork/ce-task.json
  STATUS=$(python3 -c "import json;print(json.load(open('.scannerwork/ce-task.json'))['task']['status'])")
  case "$STATUS" in SUCCESS) break ;; FAILED|CANCELED) echo "SonarQube analysis $STATUS"; exit 1 ;; esac
  sleep 3
done
[ "$STATUS" = "SUCCESS" ] || { echo "Timed out waiting for SonarQube"; exit 1; }
ANALYSIS_ID=$(python3 -c "import json;print(json.load(open('.scannerwork/ce-task.json'))['task']['analysisId'])")
curl -s -u "$AUTH" "$HOST/api/qualitygates/project_status?analysisId=$ANALYSIS_ID" > .scannerwork/gate.json
curl -s -u "$AUTH" "$HOST/api/measures/component?component=$KEY&metricKeys=bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,ncloc,reliability_rating,security_rating,sqale_rating,security_hotspots" > .scannerwork/measures.json
python3 - <<'PY'
import json, sys
gate = json.load(open(".scannerwork/gate.json"))["projectStatus"]
meas = {m["metric"]: m["value"] for m in json.load(open(".scannerwork/measures.json"))["component"]["measures"]}
rating = {"1.0": "A", "2.0": "B", "3.0": "C", "4.0": "D", "5.0": "E"}
lines = ["SonarQube report - ACEest Fitness & Gym", "=" * 44, "Quality gate : " + gate["status"], ""]
for c in gate.get("conditions", []):
    lines.append("  %-28s %-6s actual=%s threshold=%s" % (c["metricKey"], c["status"], c.get("actualValue", "-"), c.get("errorThreshold", "-")))
lines += ["", "Measures:"]
for k in ("ncloc", "bugs", "vulnerabilities", "security_hotspots", "code_smells", "coverage", "duplicated_lines_density"):
    lines.append("  %-28s %s" % (k, meas.get(k, "n/a")))
for k in ("reliability_rating", "security_rating", "sqale_rating"):
    lines.append("  %-28s %s" % (k, rating.get(meas.get(k, ""), meas.get(k, "n/a"))))
open("sonar-report.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
sys.exit(0 if gate["status"] == "OK" else 1)
PY
