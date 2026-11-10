#!/usr/bin/env bash
# Host-level wrapper. Existing per-service scripts are intentionally unchanged.
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Usage: ./services.sh {start|stop|restart|status} [--dry-run]

Manages PostgreSQL, Redis, Kafka, consumers, RustFS, FastAPI, AIOps,
Next.js, Airflow and Nginx Proxy Manager on this host.
SSH, firewall, networking and the Docker daemon are left running.

start skips services already running. restart stops the entire stack first.
Existing scripts retain their behavior: frontend start rebuilds the app;
AIOps start uses its restart command (including dependency synchronization).
Airflow stop allows 300 seconds for container shutdown; it does not pause
DAGs or guarantee completion of active tasks. Use during a maintenance window.
EOF
}

action=${1:-help}
dry_run=0
[[ $# -le 2 ]] || { usage; exit 2; }
if [[ $# == 2 ]]; then
  [[ $2 == --dry-run ]] || { usage; exit 2; }
  dry_run=1
fi
case "$action" in start|stop|restart|status) ;; help|-h|--help) usage; exit 0 ;; *) usage; exit 2 ;; esac

backend=/home/backend/eft-library-back
frontend=/home/frontend_a/eft-library-front
aiops=/home/aiops/eft-library-aiops
kafka=/home/kafka/eft-library-kafka
containers=(airflow-airflow-apiserver-1 airflow-airflow-dag-processor-1 airflow-airflow-triggerer-1 airflow-airflow-scheduler-1)

run() {
  printf '+'; printf ' %q' "$@"; printf '\n'
  if (( ! dry_run )); then "$@" 9>&-; fi
}
script() {
  local directory=$1 file=$2 operation=$3
  run bash -c 'cd -- "$1" && exec bash "$2" "$3"' _ "$directory" "$file" "$operation"
}
listening() { ss -H -ltn "sport = :$1" | grep -q .; }
wait_port() {
  local port=$1 desired=$2 deadline=$((SECONDS + 180))
  (( dry_run )) && return 0
  while :; do
    if listening "$port"; then
      [[ $desired == up ]] && return 0
    else
      [[ $desired == down ]] && return 0
    fi
    if (( SECONDS >= deadline )); then
      echo "Timed out: port $port expected $desired. Stopping here." >&2
      return 1
    fi
    sleep 1
  done
}
app() {
  local operation=$1 port=$2 directory=$3 file=$4 start_action=${5:-start}
  if [[ $operation == start ]]; then
    if (( ! dry_run )) && listening "$port"; then echo "Port $port already listening; skipped."; return; fi
    script "$directory" "$file" "$start_action"
    wait_port "$port" up
  else
    script "$directory" "$file" stop
    wait_port "$port" down
  fi
}
container() {
  local operation=$1 name=$2
  if [[ $operation == start ]]; then
    run docker start "$name"
    if (( ! dry_run )); then
      local deadline=$((SECONDS + 180)) state
      while :; do
        state=$(docker inspect -f '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "$name")
        [[ $state == 'running healthy' || $state == 'running ' ]] && break
        [[ $state != exited* && $state != dead* ]] || return 1
        (( SECONDS < deadline )) || { echo "Container not ready: $name" >&2; return 1; }
        sleep 2
      done
    fi
  else
    run docker stop --time 300 "$name"
  fi
}
consumers() {
  local operation=$1 service pid deadline
  local -a previous=()
  if [[ $operation == stop && $dry_run == 0 ]]; then
    for service in log notification; do
      if [[ -f $kafka/$service.pid ]]; then
        read -r pid < "$kafka/$service.pid"
        [[ $pid =~ ^[0-9]+$ && $pid -gt 1 ]] || return 1
        previous+=("$pid")
      fi
    done
  fi
  script "$kafka" consumer.sh "$operation"
  (( dry_run )) && return 0
  if [[ $operation == stop ]]; then
    for pid in "${previous[@]}"; do
      deadline=$((SECONDS + 180))
      while kill -0 "$pid" 2>/dev/null; do
        (( SECONDS < deadline )) || { echo "Consumer still running: $pid" >&2; return 1; }
        sleep 1
      done
    done
  else
    for service in log notification; do
      read -r pid < "$kafka/$service.pid"
      kill -0 "$pid"
    done
  fi
}
start_all() {
  run systemctl start postgresql-17
  wait_port 13245 up
  run systemctl start redis
  wait_port 6379 up
  container start rustfs
  if (( dry_run )) || ! listening 9092; then script "$kafka" kafka.sh start; fi
  wait_port 9092 up
  consumers start
  app start 9022 "$backend" restart.sh
  app start 9023 "$aiops" scripts/restart-api.sh restart
  app start 4003 "$aiops" scripts/restart-web.sh restart
  local name
  for name in "${containers[@]}"; do container start "$name"; done
  container start npm
  app start 4002 "$frontend" restart.sh
}
stop_all() {
  container stop npm
  # Stop Airflow before its APIs/storage. No DAG state is changed here.
  container stop airflow-airflow-scheduler-1
  container stop airflow-airflow-dag-processor-1
  container stop airflow-airflow-triggerer-1
  container stop airflow-airflow-apiserver-1
  app stop 4002 "$frontend" restart.sh
  app stop 4003 "$aiops" scripts/restart-web.sh
  app stop 9022 "$backend" restart.sh
  app stop 9023 "$aiops" scripts/restart-api.sh
  consumers stop
  script "$kafka" kafka.sh stop
  wait_port 9092 down
  wait_port 9093 down
  container stop rustfs
  run systemctl stop redis
  wait_port 6379 down
  run systemctl stop postgresql-17
  wait_port 13245 down
}
status_all() {
  local service port
  for service in postgresql-17 redis docker; do
    printf '%-20s ' "$service"
    systemctl is-active "$service" || true
  done
  docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
  for port in 13245 6379 9092 9093 9022 9023 4002 4003 9000 9001 13001 80 81 443; do
    if listening "$port"; then printf '%-8s LISTEN\n' "$port"; else printf '%-8s CLOSED\n' "$port"; fi
  done
  script "$kafka" kafka.sh status
  script "$aiops" restart.sh status || true
}

if [[ $action != status && $dry_run == 0 ]]; then
  [[ $EUID == 0 ]] || { echo 'Run with sudo (preserve PATH for pnpm/uv if needed).' >&2; exit 1; }
  exec 9>/run/eft-library-services.lock
  flock -n 9 || { echo 'Another service operation is running.' >&2; exit 1; }
fi
trap 'echo "Failed at line $LINENO; remaining operations were not run." >&2' ERR
case "$action" in
  start) start_all ;;
  stop) stop_all ;;
  restart) stop_all; start_all ;;
  status) status_all ;;
esac
