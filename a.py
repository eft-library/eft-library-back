import requests


def run_query(query):
    headers = {"Content-Type": "application/json"}
    response = requests.post('https://api.tarkov.dev/graphql', headers=headers, json={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(response.status_code, query))


new_query = """
{
         items {
            id
            name
            shortName
            image512pxLink
            category {
              name
              parent {
                name
              }
            }
            properties {
              ... on ItemPropertiesMelee {
            slashDamage
            stabDamage
            hitRadius
            }
          }
        }
    }
"""

result = run_query(new_query)

for item in result['data']['items']:
    if item['category']['name'] == "Throwable weapon":
        print(item)
