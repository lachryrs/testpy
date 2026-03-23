import os
import yaml
from fastapi import FastAPI
import databases
from logging import getLogger
from endpoint_types.query_endpoint import QueryEndpoint

DATABASE_URL = "sqlite:///./test.db"
database = databases.Database(DATABASE_URL)
logger = getLogger('app.start')
app = FastAPI()

def load_yaml_endpoints(folder: str = "endpoints"):
    query_endpoint = QueryEndpoint(app, database)

    for filename in os.listdir(folder):
        if not filename.endswith(".yaml"):
            continue

        with open(os.path.join(folder, filename)) as f:
            config = yaml.safe_load(f)

        logger.info(f'Loaded yaml: {filename}')

        base_route = config.get("base_route")
        if not base_route:
            raise Exception(f'No base_route supplied in {filename}.')

        for endpoint in config.get("query", []):
            print(f'{endpoint=}')
            query_endpoint.make_endpoint(base_route, endpoint)


load_yaml_endpoints()
print([route.path for route in app.routes])

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()