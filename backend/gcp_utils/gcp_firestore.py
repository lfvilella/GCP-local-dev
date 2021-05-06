"""GCP Firestore helper module."""
from google.auth import credentials
from google.cloud import firestore
from . import gcp_env


def _get_firestore_client() -> firestore.Client:
    kwargs = {}
    if not gcp_env.is_prod():
        kwargs["credentials"] = credentials.AnonymousCredentials()
    return firestore.Client(**kwargs)


DB = _get_firestore_client()
