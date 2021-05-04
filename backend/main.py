import csv
import datetime
import io
import os
import uuid
import typing

import fastapi
import fastapi.responses
import pydantic
import uvicorn

from google.auth import credentials
from google.cloud import storage
from google.cloud import firestore
from google.cloud import ndb


class ItemNdb(ndb.Model):
    # id: uuid4
    name: str = ndb.StringProperty(required=True)
    price: float = ndb.FloatProperty(required=True)
    is_offer: typing.Optional[bool] = ndb.BooleanProperty(required=False)
    created_at: typing.Optional[datetime.datetime] = ndb.DateTimeProperty(
        auto_now_add=True
    )


class ItemCreateSchema(pydantic.BaseModel):
    name: str
    price: pydantic.PositiveFloat
    is_offer: typing.Optional[bool] = False


class ItemDetailSchema(ItemCreateSchema):
    id: uuid.UUID
    created_at: datetime.datetime

    @classmethod
    def load_from_ndb(cls, item: ItemNdb) -> "ItemDetailSchema":
        return ItemDetailSchema(id=item.key.id(), **item.to_dict())


def _is_prod() -> bool:
    return os.getenv("SERVER_SOFTWARE", "").startswith("Google App Engine/")


def _get_storage_client() -> storage.Client:
    kwargs = {}
    if not _is_prod():
        kwargs["credentials"] = credentials.AnonymousCredentials()
    return storage.Client(**kwargs)


def _get_firestore_client() -> firestore.Client:
    kwargs = {}
    if not _is_prod():
        kwargs["credentials"] = credentials.AnonymousCredentials()
    return firestore.Client(**kwargs)


_STORAGE_CLIENT = _get_storage_client()
_FIRESTORE_CLIENT = _get_firestore_client()
_NDB_CLIENT = ndb.Client()


async def ndb_context():
    with _NDB_CLIENT.context():
        yield


def _generate_csv():
    rows = []
    for item in ItemNdb.query().fetch():
        data = item.to_dict()
        data["id"] = item.key.id()
        rows.append(data)

    if not rows:
        return

    bucket_name = "tmp-bucket"
    bucket = _STORAGE_CLIENT.lookup_bucket(bucket_name)
    if not bucket:
        bucket = _STORAGE_CLIENT.create_bucket(bucket_name)

    with io.StringIO() as f:
        fieldnames = sorted(rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

        filename = f"items-{datetime.datetime.utcnow()}.csv"
        blob = bucket.blob(filename)
        blob.upload_from_string(f.getvalue(), content_type="text/csv")


def _update_realtime_db(item_id: uuid.UUID):
    item = ItemNdb.get_by_id(item_id)
    doc_ref = _FIRESTORE_CLIENT.collection("items").document(item.key.id())
    doc_ref.set(item.to_dict())


def _create_item(item_to_create: ItemCreateSchema) -> ItemDetailSchema:
    # insert into NDB
    item_ndb = ItemNdb(id=str(uuid.uuid4()), **item_to_create.dict())
    item_ndb.put()

    # update realtime DB
    _update_realtime_db(item_ndb.key.id())

    # generate a CSV file
    _generate_csv()

    return ItemDetailSchema.load_from_ndb(item_ndb)


app = fastapi.FastAPI()


@app.get("/")
def hello():
    return {"msg": "hello"}


@app.post(
    "/item",
    response_model=ItemDetailSchema,
    status_code=201,
    dependencies=[fastapi.Depends(ndb_context)],
)
def item_create(item: ItemCreateSchema):
    return _create_item(item)


@app.get(
    "/item/{item_id}",
    response_model=ItemDetailSchema,
    dependencies=[fastapi.Depends(ndb_context)],
)
def item_detail(item_id: uuid.UUID):
    item_ndb = ItemNdb.get_by_id(str(item_id))
    if not item_ndb:
        raise fastapi.HTTPException(status_code=404, detail="Item not found")

    return ItemDetailSchema.load_from_ndb(item_ndb)


@app.get(
    "/items",
    response_model=typing.List[ItemDetailSchema],
    dependencies=[fastapi.Depends(ndb_context)],
)
def item_list():
    items = []
    for item_ndb in ItemNdb.query().fetch():
        items.append(ItemDetailSchema.load_from_ndb(item_ndb))

    return items


@app.get("/gcp-files", response_model=typing.List[str])
def gcs_files():
    files = []
    for bucket in _STORAGE_CLIENT.list_buckets():
        for blob in _STORAGE_CLIENT.list_blobs(bucket):
            files.append(f"{bucket.name}/{blob.name}")
    return files


@app.get("/gcp-file/{bucket_name}/{filename}")
def gcs_file(bucket_name: str, filename: str):
    bucket = _STORAGE_CLIENT.lookup_bucket(bucket_name)
    if not bucket:
        raise fastapi.HTTPException(status_code=404, detail="csv not found")

    blob = bucket.get_blob(filename)
    if not bucket:
        raise fastapi.HTTPException(status_code=404, detail="csv not found")

    data = blob.download_as_string()

    response = fastapi.responses.StreamingResponse(
        iter([data]), media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=export.csv"

    return response


@app.get("/app-env")
def app_env():
    return {"SERVER_SOFTWARE": os.getenv("SERVER_SOFTWARE", "")}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, debug=True, reload=True)
