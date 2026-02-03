#!/bin/bash

. venv/bin/activate

DEFAULT_PORT=9022
ACTION=$1
PORT=${2:-$DEFAULT_PORT}
PID_FILE=uvicorn.pid

start_server() {
  if [ -f $PID_FILE ]; then
    echo "이미 실행 중입니다 (PID: $(cat $PID_FILE))"
    exit 1
  fi

  echo "FastAPI 서버 실행 (포트 $PORT)"
  nohup uvicorn main:app \
    --workers 9 \
    --host=0.0.0.0 \
    --port=$PORT \
    --no-access-log \
    > log.out 2>&1 &

  echo $! > $PID_FILE
}

stop_server() {
  if [ ! -f $PID_FILE ]; then
    echo "실행 중인 서버가 없습니다"
    return
  fi

  PID=$(cat $PID_FILE)
  echo "FastAPI 서버 종료 (PID: $PID)"

  kill -TERM $PID

  # graceful wait
  for i in {1..10}; do
    if ps -p $PID > /dev/null; then
      sleep 1
    else
      break
    fi
  done

  # still alive → force kill
  if ps -p $PID > /dev/null; then
    echo "강제 종료(SIGKILL)"
    kill -9 $PID
  fi

  rm -f $PID_FILE
}

case "$ACTION" in
  start) start_server ;;
  stop) stop_server ;;
  restart) stop_server && sleep 1 && start_server ;;
  *) echo "사용법: $0 {start|stop|restart} [포트번호]" ;;
esac

deactivate
