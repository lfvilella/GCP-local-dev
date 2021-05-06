"""GCP Datastore helper module."""
from google.cloud import ndb


_client = ndb.Client()


async def ndb_context():
    with _client.context():
        yield
