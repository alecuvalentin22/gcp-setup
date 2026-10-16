#!/bin/sh
set -eu
for values in dev prod; do
  helm lint charts/podinfo-app -f "charts/podinfo-app/values-${values}.yaml"
done
