import typing
import os

import fastapi
import fastapi.responses
import uvicorn

import gcp_utils
import models
import services


app = fastapi.FastAPI()
ndb_dependecy = fastapi.Depends(gcp_utils.datastore.ndb_context)


@app.get("/")
async def hello():
    return {"msg": "hello"}


@app.post(
    "/item",
    response_model=models.ItemDetailPyd,
    status_code=201,
    dependencies=[ndb_dependecy],
)
async def item_create(item: models.ItemCreatePyd):
    return services.create_item(item)


@app.get(
    "/item/{item_id}",
    response_model=models.ItemDetailPyd,
    dependencies=[ndb_dependecy],
)
async def item_detail(item_id: models.ItemNdb.TID):
    item = services.get_item(item_id)
    if not item:
        raise fastapi.HTTPException(status_code=404, detail="Item not found")

    return item


@app.get(
    "/items",
    response_model=typing.List[models.ItemDetailPyd],
    dependencies=[ndb_dependecy],
)
async def item_list():
    return services.get_all_items()


@app.get("/gcs-files", response_model=typing.List[str])
async def gcs_files():
    return services.list_all_cloud_storage_files()


@app.get("/gcs-file/{bucket_name}/{filename}")
async def gcs_file(bucket_name: str, filename: str):
    blob = gcp_utils.cloud_storage.get_file(bucket_name, filename)
    if not blob:
        raise fastapi.HTTPException(status_code=404, detail="csv not found")

    data = blob.download_as_string()

    response = fastapi.responses.StreamingResponse(
        iter([data]), media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=export.csv"

    return response


@app.post(
    gcp_utils.tasks.TASK_EXEC_HANDLER,
    dependencies=[ndb_dependecy],
)
async def tesks_exec(payload: gcp_utils.tasks.TaskPayload):
    gcp_utils.tasks.exec_task(payload)


@app.get("/app-env")
def app_env():
    return {"SERVER_SOFTWARE": os.getenv("SERVER_SOFTWARE", "")}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, debug=True, reload=True)
