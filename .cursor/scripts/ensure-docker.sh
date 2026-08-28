#!/usr/bin/env bash
#
# ensure-docker.sh
#
# Idempotently prepare and start a Docker daemon that works inside the
# Cursor Cloud Agent VM (a container running on an overlay filesystem).
#
# Two environment-specific adjustments are required here and are safe to
# re-apply on every invocation:
#
#   1. Storage driver: the VM root is an overlay mount, so the default
#      overlayfs/containerd snapshotter cannot mount images. The "vfs"
#      driver works reliably in this nested setup.
#
#   2. Bridge networking: this host ships a stale iptables-legacy filter
#      table whose FORWARD policy is DROP with empty Docker chains. Because
#      bridge-nf-call-iptables is enabled, container-to-container traffic
#      traverses that legacy hook and is dropped. Docker only programs the
#      nft tables, so we open the legacy FORWARD policy. Container isolation
#      is still enforced by Docker's nft DOCKER rules.
set -euo pipefail

log() { echo "[ensure-docker] $*"; }

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    return 0
  fi
  log "Docker not found; installing via get.docker.com"
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sudo sh /tmp/get-docker.sh
}

write_daemon_config() {
  sudo mkdir -p /etc/docker
  local desired
  desired='{
  "storage-driver": "vfs",
  "features": { "containerd-snapshotter": false }
}'
  if [ ! -f /etc/docker/daemon.json ] || [ "$(cat /etc/docker/daemon.json)" != "$desired" ]; then
    log "Writing /etc/docker/daemon.json (vfs storage driver)"
    echo "$desired" | sudo tee /etc/docker/daemon.json >/dev/null
  fi
}

start_daemon() {
  if sudo docker info >/dev/null 2>&1; then
    log "Docker daemon already running"
    return 0
  fi
  log "Starting dockerd"
  sudo bash -c 'nohup dockerd >/var/log/dockerd.log 2>&1 &'
  local deadline=$(( $(date +%s) + 60 ))
  until sudo docker info >/dev/null 2>&1; do
    if [ "$(date +%s)" -ge "$deadline" ]; then
      log "ERROR: dockerd did not become ready within 60s"
      sudo tail -n 40 /var/log/dockerd.log || true
      exit 1
    fi
    sleep 2
  done
  log "Docker daemon is ready"
}

fix_bridge_networking() {
  if command -v iptables-legacy >/dev/null 2>&1; then
    if [ "$(sudo iptables-legacy -L FORWARD -n 2>/dev/null | awk 'NR==1{print $4}')" != "ACCEPT)" ]; then
      log "Opening iptables-legacy FORWARD policy for bridge networking"
      sudo iptables-legacy -P FORWARD ACCEPT || true
    fi
  fi
}

grant_socket_access() {
  # Let the non-root environment user run docker without sudo.
  if [ -S /var/run/docker.sock ]; then
    sudo chmod 666 /var/run/docker.sock || true
  fi
}

install_docker
write_daemon_config
start_daemon
fix_bridge_networking
grant_socket_access

log "Docker is ready: $(docker --version 2>/dev/null || sudo docker --version)"
