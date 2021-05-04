import os
import uuid

from flask import Flask

from google.auth import credentials
from google.cloud import storage
from google.cloud import firestore
from google.cloud import ndb


class BookModel(ndb.Model):
    title = ndb.StringProperty()


app = Flask(__name__)


def is_prod() -> bool:
    return os.getenv("SERVER_SOFTWARE", "").startswith("Google App Engine/")


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/ndb")
def ndb_handler():
    with ndb.Client().context():
        total = BookModel.query().count()
    return f"total books {total}"


def _get_storage_client() -> storage.Client:
    kwargs = {}
    if not is_prod():
        kwargs["credentials"] = credentials.AnonymousCredentials()
    return storage.Client(**kwargs)


@app.route("/storage")
def storage_handler():
    client = _get_storage_client()

    bucket_name = "tmp-bucket"
    bucket = client.lookup_bucket(bucket_name)
    if not bucket:
        bucket = client.create_bucket(bucket_name)

    filename = f"testfile-{uuid.uuid4()}.txt"

    blob = bucket.blob(filename)
    string = f"new string -> {uuid.uuid4()}"
    blob.upload_from_string(string)

    return bucket.get_blob(filename).download_as_string()


def _get_firestore_client() -> firestore.Client:
    kwargs = {}
    if not is_prod():
        kwargs["credentials"] = credentials.AnonymousCredentials()
    return firestore.Client(**kwargs)


@app.route("/firestore")
def firestore_handler():
    db = _get_firestore_client()
    doc_ref = db.collection("users").document("alovelace")
    doc_ref.set({"first": "Ada", "last": "Lovelace", "born": 1815})

    users_ref = db.collection("users")

    users = []
    for doc in users_ref.stream():
        users.append("{} => {}".format(doc.id, doc.to_dict()))

    return f"{users}"


@app.route("/app-env")
def app_env():
    return os.getenv("SERVER_SOFTWARE", "")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
