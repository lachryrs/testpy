import inspect
from fastapi import HTTPException
from pydantic import create_model
from typing import List

TYPE_MAP = {
    "int": int,
    "str": str,
    "float": float,
    "bool": bool,
}

class QueryEndpoint:
    def __init__(self, app, database):
        self.app = app
        self.database = database

    def make_response_model(self, name: str, response_fields: list):
        fields = {
            f["name"]: (TYPE_MAP.get(f["type"], str), ...)
            for f in response_fields
        }
        return create_model(name, **fields)


    def make_endpoint(self, base_route: str, definition: dict):
        path_suffix = definition.get("path", "")
        full_path = f"{base_route}{path_suffix}"
        sql = definition.get("sql")
        query_params = definition.get("query_params", [])
        path_params = definition.get("path_params", [])
        summary = definition.get("summary", "")
        method = definition.get("method")
        name = definition.get("name", full_path)
        response_fields = definition.get("response_fields")

        if method != "GET":
            print(f'Skipping creation of endpoint for {full_path}, query endpoint type only supports GETs.')
            return

        if not response_fields:
            print(f'Skipping creation of endpoint for {full_path}, query endpoint must have atleast one response field.')
            return
        
        for field in response_fields:
            print(f'{field=}')
            if not field.get('name'):
                print(f'Skipping creation of endpoint for {full_path}, response field must have a name to define the column to return.')
                return
            if not field.get('type'):
                print(f'Skipping creation of endpoint for {full_path}, response field must have a type to define the column type to return.')
                return
            
        existing = [
            r for r in self.app.routes
            if hasattr(r, 'path') and r.path == full_path
            and method.upper() in r.methods
        ]
        if existing:
            print(f'Duplicate endpoint path detected for {full_path}, skipping creation.')


        response_model = None
        if response_fields:
            model = self.make_response_model(name.replace(" ", "_"), response_fields)
            response_model = List[model]

        handler = self.make_handler(sql, query_params, path_params)

        self.app.add_api_route(
            path=full_path,
            endpoint=handler,
            methods=[method.upper()],
            summary=summary,
            name=name,
            response_model=response_model,
        )

    def make_handler(self, sql: str, query_params: list, path_params: list):
        database = self.database

        default_query_params = [
            {"name": "limit", "type": "int", "default": 100},
            {"name": "offset", "type": "int", "default": 0},
        ]
        all_query_params = default_query_params + query_params

        params = {}
        for p in path_params:
            params[p["name"]] = inspect.Parameter(
                p["name"],
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=TYPE_MAP.get(p["type"], str),
            )

        for p in all_query_params:
            default = p.get("default", inspect.Parameter.empty)
            params[p["name"]] = inspect.Parameter(
                p["name"],
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
                annotation=TYPE_MAP.get(p["type"], str),
            )

        sig = inspect.Signature(list(params.values()))

        async def handler(**kwargs):
            if sql:
                try:
                    rows = await database.fetch_all(query=sql, values=kwargs)
                    return [dict(row) for row in rows]
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
            return kwargs

        handler.__signature__ = sig
        return handler