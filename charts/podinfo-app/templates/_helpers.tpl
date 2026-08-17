{{/*
Helpers exist so names are computed once. Hardcoding names in each template is
how you end up with a Service whose selector no longer matches its Deployment.
*/}}

{{- define "podinfo-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "podinfo-app.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "podinfo-app.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Labels applied to every object. app.kubernetes.io/* are the Kubernetes
recommended labels; tooling (kubectl, dashboards, ArgoCD) understands them.
*/}}
{{- define "podinfo-app.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{ include "podinfo-app.selectorLabels" . }}
{{- end -}}

{{/*
Selector labels are a SEPARATE, smaller set on purpose.
A Deployment's spec.selector is IMMUTABLE. If version-bearing labels were in
the selector, every chart upgrade would try to mutate it and fail with
"field is immutable" — forcing a delete/recreate of the Deployment.
*/}}
{{- define "podinfo-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "podinfo-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
