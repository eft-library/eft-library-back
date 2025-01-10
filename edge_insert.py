import json
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL에 연결
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

# 커서 생성
cur = conn.cursor()

# JSON 파일 경로
file_path = "./node.json"

# JSON 파일 읽기
with open(file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# 반복문을 통해 JSON 데이터 처리
for node in data:
    node_id = node['id']
    npc_value = node['data']['npc']

    # 먼저 UPDATE 실행 (해당 id가 있을 경우 업데이트)
    update_query = """
        UPDATE tkl_roadmap_node
        SET npc_value = %s
        WHERE id = %s;
    """
    cur.execute(update_query, (npc_value, node_id))

# for edge in data:
#     edge_id = edge['id']
#     edge_source = edge['source']
#     edge_target = edge['target']
#
#     insert_query = """
#         INSERT INTO tkl_roadmap_edge (id, source_id, target_id, update_time)
#         VALUES (%s, %s, %s, now());
#     """
#
#     cur.execute(insert_query, (edge_id, edge_source, edge_target))

# 변경 사항 커밋
conn.commit()

# 커서와 연결 닫기
cur.close()
conn.close()
