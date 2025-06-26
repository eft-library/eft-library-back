#!/bin/bash

ACTION=$1  # 'start' 또는 'stop'

if [[ "$ACTION" != "start" && "$ACTION" != "stop" ]]; then
  echo "Usage: $0 {start|stop}"
  exit 1
fi

# ▶️ Next.js
manage_nextjs() {
  echo "🔧 Next.js: $ACTION"
  /home/frontend_a/eft-library-front/restart_a.sh "$ACTION"
}

# ▶️ FastAPI
manage_fastapi() {
  echo "🔧 FastAPI: $ACTION"
  /home/backend/eft-library-back/restart.sh "$ACTION"
}

# ▶️ Kafka
manage_kafka() {
  echo "🔧 Kafka: $ACTION"
  if [ "$ACTION" = "stop" ]; then
    /home/kafka/eft-library-kafka/consumer.sh stop
    /home/kafka/kafka_2.13-4.0.0/bin/kafka-server-stop.sh
  else
    /home/kafka/kafka_2.13-4.0.0/bin/kafka-storage.sh format \
      --config /home/kafka/kafka_2.13-4.0.0/config/server.properties \
      --cluster-id $(""/home/kafka/kafka_2.13-4.0.0/bin/kafka-storage.sh"" random-uuid) \
      --standalone

    /home/kafka/kafka_2.13-4.0.0/bin/kafka-server-start.sh -daemon \
      /home/kafka/kafka_2.13-4.0.0/config/server.properties

    /home/kafka/eft-library-kafka/consumer.sh start
  fi
}

# ▶️ ClickHouse
manage_clickhouse() {
  echo "🔧 ClickHouse: $ACTION"
  sudo systemctl "$ACTION" clickhouse-server
}

# ▶️ PostgreSQL
manage_postgresql() {
  echo "🔧 PostgreSQL: $ACTION"
  sudo systemctl "$ACTION" postgresql
}

# ▶️ MinIO
manage_minio() {
  echo "🔧 MinIO: $ACTION"
  sudo systemctl "$ACTION" minio
}

# ▶️ Airflow
manage_airflow() {
  echo "🔧 Airflow: $ACTION"
  if [ "$ACTION" = "stop" ]; then
    docker stop 861824de8429
  else
    docker start 861824de8429
    docker exec -d airflow airflow scheduler
  fi
}

# ▶️ Nginx Proxy Manager
manage_nginx_proxy() {
  echo "🔧 Nginx Proxy Manager: $ACTION"
  if [ "$ACTION" = "stop" ]; then
    docker stop 44b959f4357e
  else
    docker start 44b959f4357e
  fi
}

# ▶️ 모든 서비스 실행
main() {
  echo "===== [$ACTION] 모든 서비스 제어 시작 ====="
  manage_nextjs
  manage_fastapi
  manage_kafka
  manage_clickhouse
  manage_postgresql
  manage_minio
  manage_airflow
  manage_nginx_proxy
  echo "===== [$ACTION] 모든 서비스 제어 완료 ====="
}

main
