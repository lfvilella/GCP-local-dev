"""Backend services."""
import typing
import datetime

import gcp_utils
import models


def _generate_csv():
    rows = []
    for item in models.ItemNdb.query().fetch():
        data = item.to_dict()
        data["id"] = item.key.id()
        rows.append(data)

    if not rows:
        return

    filename = f"items-{datetime.datetime.utcnow()}.csv"
    gcp_utils.cloud_storage.write_csv(
        gcp_utils.cloud_storage.BucketName.TMP_FILES, filename, rows
    )


def _update_realtime_db(item_id: models.ItemNdb.TID):
    item = models.ItemNdb.get_by_id(item_id)
    doc_ref = gcp_utils.firestore.DB.collection("items").document(item.key.id())
    doc_ref.set(item.to_dict())


def create_item(item_to_create: models.ItemCreatePyd) -> models.ItemDetailPyd:
    # insert into NDB
    item_ndb = models.ItemNdb(
        id=models.ItemNdb.generate_id(),
        **item_to_create.dict(),
    )
    item_ndb.put()

    # update realtime DB
    gcp_utils.tasks.defer_execution(
        _update_realtime_db, item_id=item_ndb.key.id(), _delay_in_seconds=5
    )

    # generate a CSV file
    gcp_utils.tasks.defer_execution(_generate_csv, _delay_in_seconds=10)

    return models.ItemDetailPyd.load_from_ndb(item_ndb)


def get_item(
    item_id: models.ItemNdb.TID,
) -> typing.Optional[models.ItemDetailPyd]:
    item = models.ItemNdb.get_by_id(item_id)
    if item:
        return models.ItemDetailPyd.load_from_ndb(item)


def filter_items(
    filters: typing.Optional[models.ItemFiltersPyd] = None,
) -> typing.List[models.ItemDetailPyd]:
    filters = filters or models.ItemFiltersPyd()

    query = models.ItemNdb.query()

    if filters.name_startswith is not None:
        query = query.filter(models.ItemNdb.name >= filters.name_startswith)

    if filters.is_offer is not None:
        query = query.filter(models.ItemNdb.is_offer == filters.is_offer)

    if filters.min_price is not None:
        query = query.filter(models.ItemNdb.price >= filters.min_price)

    if filters.max_price is not None:
        query = query.filter(models.ItemNdb.price < filters.max_price)

    items = [
        models.ItemDetailPyd.load_from_ndb(item_ndb)
        for item_ndb in query.fetch()
    ]
    return items


def get_offers_in_price_range(
    min_price: typing.Optional[float] = None,
    max_price: typing.Optional[float] = None,
) -> typing.List[models.ItemDetailPyd]:
    return filter_items(
        models.ItemFiltersPyd(
            is_offer=True, min_price=min_price, max_price=max_price
        )
    )


def list_all_cloud_storage_files() -> typing.List[str]:
    files = []
    for bucket in gcp_utils.cloud_storage.CLIENT.list_buckets():
        for blob in gcp_utils.cloud_storage.CLIENT.list_blobs(bucket):
            files.append(f"{bucket.name}/{blob.name}")
    return files
