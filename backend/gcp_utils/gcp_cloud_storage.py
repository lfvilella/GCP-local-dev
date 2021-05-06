"""GCP cloud storage helper module."""
import csv
import enum
import io
import typing

from google.auth import credentials
from google.cloud import storage
from . import gcp_env


def _get_storage_client() -> storage.Client:
    kwargs = {}
    if not gcp_env.is_prod():
        kwargs["credentials"] = credentials.AnonymousCredentials()
    return storage.Client(**kwargs)


CLIENT = _get_storage_client()


class BucketName(enum.Enum):
    TMP_FILES = "tmp_files"


def get_bucket(bucket_name: BucketName) -> typing.Optional[storage.Bucket]:
    return CLIENT.lookup_bucket(bucket_name.value)


def _get_or_create_bucket(bucket_name: BucketName) -> storage.Bucket:
    bucket = get_bucket(bucket_name)
    if bucket:
        return bucket

    return CLIENT.create_bucket(bucket_name.value)


def write_csv(
    bucket_name: BucketName,
    filename: str,
    rows: typing.List[typing.Dict[str, typing.Any]],
) -> storage.Blob:

    bucket = _get_or_create_bucket(bucket_name)
    blob = bucket.blob(filename)

    with io.StringIO() as f:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

        blob.upload_from_string(f.getvalue(), content_type="text/csv")

    return blob


def get_file(
    bucket_name: typing.Union[BucketName, str], filename: str
) -> typing.Optional[storage.Blob]:
    if isinstance(bucket_name, str):
        try:
            bucket_name = BucketName(bucket_name)
        except ValueError:
            return

    bucket = get_bucket(bucket_name)
    if bucket:
        return bucket.get_blob(filename)
