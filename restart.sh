#!/bin/bash

# 가상환경 활성화
. venv/bin/activate

# 기본 포트
DEFAULT_PORT=9022

# 인자 처리
ACTION=$1
PORT=${2:-$DEFAULT_PORT}  # 두 번째 인자가 없으면 기본값 사용

# 프로세스 종료 함수
stop_server() {
  pid=$(netstat -tnlp 2>/dev/null | grep ":$PORT\b" | awk '{print $7}' | cut -d'/' -f1)
  if [ -n "$pid" ]; then
    echo "포트 $PORT를 사용 중인 프로세스(PID: $pid)를 종료합니다."
    kill -9 "$pid"
    sleep 1
  else
    echo "포트 $PORT를 사용 중인 프로세스가 없습니다."
  fi
}

# 서버 시작 함수
start_server() {
  echo "FastAPI 서버를 포트 $PORT에서 실행합니다."
  nohup uvicorn main:app --reload --host=0.0.0.0 --port=$PORT > log.out 2>&1 &
}

# 명령 분기
case "$ACTION" in
  start)
    start_server
    ;;
  stop)
    stop_server
    ;;
  restart)
    stop_server
    start_server
    ;;
  *)
    echo "사용법: $0 {start|stop|restart} [포트번호]"
    exit 1
    ;;
esac

# 가상환경 비활성화
deactivate
