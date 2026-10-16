FROM alpine:3.20 AS tools

# Pinned task tools. Official release checksum manifests are verified before
# installation; TARGETARCH supports Docker's amd64 and arm64 builds.
ARG TARGETARCH
ARG HELM_VERSION=v3.16.4
ARG YQ_VERSION=v4.44.3
RUN apk add --no-cache curl tar coreutils
RUN set -eu; \
    case "$TARGETARCH" in amd64) arch=amd64 ;; arm64) arch=arm64 ;; *) echo "unsupported architecture: $TARGETARCH" >&2; exit 1 ;; esac; \
    helm_file="helm-${HELM_VERSION}-linux-${arch}.tar.gz"; \
    curl -fsSLo "/tmp/${helm_file}" "https://get.helm.sh/${helm_file}"; \
    curl -fsSLo "/tmp/${helm_file}.sha256sum" "https://get.helm.sh/${helm_file}.sha256sum"; \
    (cd /tmp && sha256sum -c "${helm_file}.sha256sum"); \
    tar -xzf "/tmp/${helm_file}" -C /tmp; install -m 0755 "/tmp/linux-${arch}/helm" /usr/local/bin/helm; \
    yq_file="yq_linux_${arch}"; \
    curl -fsSLo /tmp/yq "https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/${yq_file}"; \
    curl -fsSLo /tmp/yq.sha256 "https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/checksums"; \
    expected="$(awk -v f="$yq_file" '$2 == f {print $1}' /tmp/yq.sha256)"; \
    test -n "$expected"; printf '%s  %s\n' "$expected" /tmp/yq | sha256sum -c -; \
    install -m 0755 /tmp/yq /usr/local/bin/yq; rm -rf "/tmp/${helm_file}" "/tmp/${helm_file}.sha256sum" /tmp/linux-* /tmp/yq /tmp/yq.sha256

FROM semaphoreui/semaphore:v2.19.12
COPY --from=tools /usr/local/bin/helm /usr/local/bin/helm
COPY --from=tools /usr/local/bin/yq /usr/local/bin/yq

# Keep this image definition explicit so a local rebuild uses the same
# Semaphore release as the existing service.
