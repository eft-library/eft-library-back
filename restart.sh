#!/bin/bash

. venv/bin/activate

DEFAULT_PORT=9022
ACTION=$1
PORT=${2:-$DEFAULT_PORT}

stop_server() {
  fuser -k ${PORT}/tcp 2>/dev/null
}

start_server() {
  echo "FastAPI 서버 실행 (포트 $PORT)"
  nohup uvicorn main:app --reload --host=0.0.0.0 --port=$PORT --no-access-log > log.out 2>&1 &
}

case "$ACTION" in
  start) start_server ;;
  stop) stop_server ;;
  restart) stop_server && sleep 1 && start_server ;;
  *) echo "사용법: $0 {start|stop|restart} [포트번호]" ;;
esac

deactivate
