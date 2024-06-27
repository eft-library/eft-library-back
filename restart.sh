#!/bin/bash

# 포트 번호를 첫 번째 인수로 받아옴
port=9010

# 해당 포트를 사용 중인 프로세스의 PID를 찾아서 변수에 저장
pid=$(netstat -tnlp | grep ":$port\b" | awk '{print $7}' | cut -d'/' -f1)

# PID가 비어있는지 확인하고, 비어있지 않으면 프로세스를 종료
if [ -n "$pid" ]; then
  echo "포트 $port를 사용 중인 프로세스의 PID: $pid"
  echo "프로세스를 종료합니다."
  kill -9 "$pid"
else
  echo "포트 $port를 사용 중인 프로세스가 없습니다."
fi

sleep 1

piid=$(netstat -tnlp | grep ":$port\b" | awk '{print $7}' | cut -d'/' -f1)

# PID가 비어있는지 확인하고, 비어있지 않으면 프로세스를 종료
if [ -n "$piid" ]; then
  echo "포트 $port를 사용 중인 프로세스의 PID: $piid"
  echo "프로세스를 종료합니다."
  kill -9 "$piid"
else
  echo "포트 $port를 사용 중인 프로세스가 없습니다."
fi

sleep 1

nohup uvicorn main:app --reload --host=0.0.0.0 --port=9010 > log.out 2>&1 &