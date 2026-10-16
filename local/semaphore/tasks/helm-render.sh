#!/bin/sh
set -eu
for values in dev prod; do
  helm template podinfo charts/podinfo-app -f "charts/podinfo-app/values-${values}.yaml" >/dev/null
done
