#!/bin/zsh
# Wait until forums.ohdsi.org answers, then run the paced collector. Retries every 10 min for up to ~6 h.
cd "$(dirname "$0")/.."
for i in {1..360}; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -m 20 -A "rhino-ohdsi-community-research/0.1 (daniel@rhinohealth.com)" "https://forums.ohdsi.org/about.json")
  if [ "$code" = "200" ]; then echo "$(date) forum reachable; starting collector"; exec python3 collect/forums.py; fi
  echo "$(date) forum not reachable (http $code), attempt $i; sleeping 60s"; sleep 60
done
echo "$(date) gave up waiting for forum"; exit 1
