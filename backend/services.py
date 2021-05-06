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


def get_all_items() -> typing.List[models.ItemDetailPyd]:
    items = []
    for item_ndb in models.ItemNdb.query().fetch():
        items.append(models.ItemDetailPyd.load_from_ndb(item_ndb))
    return items


def list_all_cloud_storage_files() -> typing.List[str]:
    files = []
    for bucket in gcp_utils.cloud_storage.CLIENT.list_buckets():
        for blob in gcp_utils.cloud_storage.CLIENT.list_blobs(bucket):
            files.append(f"{bucket.name}/{blob.name}")
    return files
