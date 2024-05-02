import requests
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

def run_query(query):
    headers = {"Content-Type": "application/json"}
    response = requests.post('https://api.tarkov.dev/graphql', headers=headers, json={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(response.status_code, query))

conn = psycopg2.connect(
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    port=os.getenv("DB_PORT")
)

cur = conn.cursor()

new_query = """
{
    items{
        id
        name
        shortName
        updated
        width
        height
        iconLink
        gridImageLink
        types
        accuracyModifier
        recoilModifier
        ergonomicsModifier
        hasGrid
        blocksHeadphones
        link
        weight
        velocity
        loudness
    }
}
"""

result = run_query(new_query)
insert_query = """INSERT INTO tkw_dev_item (id, name, short_name, updated, width, height, icon_link, 
                      grid_image_link, types, accuracy_modifier, recoil_modifier, ergonomics_modifier, has_grid, 
                      blocks_headphones, link, weight, velocity, loudness) 
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

for item in result['data']['items']:
    cur.execute(insert_query, (item['id'], item['name'], item['shortName'], item['updated'], item['width'], item['height'], item['iconLink'], item['gridImageLink'], item['types'], item['accuracyModifier'], item['recoilModifier'], item['ergonomicsModifier'], item['hasGrid'], item['blocksHeadphones'], item['link'], item['weight'], item['velocity'], item['loudness']))

conn.commit()
cur.close()
conn.close()