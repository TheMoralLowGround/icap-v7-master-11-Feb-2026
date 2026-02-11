{{/*
Template for environment variable from Values with quote
Usage: {{ include "env.fromValues" (dict "name" "DEBUG" "path" .Values.backend.common.env.DEBUG) | nindent 12 }}
*/}}
{{- define "env.fromValues" -}}
- name: {{ .name }}
  value: {{ .path | quote }}
{{- end -}}

{{/*
Simplified template for secret with Release.Name prefix
Usage: {{ include "env.fromReleaseSecret" (dict "name" "DB_NAME" "suffix" "backend-postgres-db-creds" "key" "DB_NAME" "context" .) | nindent 12 }}
*/}}
{{- define "env.fromReleaseSecret" -}}
- name: {{ .name }}
  valueFrom:
    secretKeyRef:
      name: {{ .context.Release.Name }}-{{ .suffix }}
      key: {{ .key }}
{{- end -}}