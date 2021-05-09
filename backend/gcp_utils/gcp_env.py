"""GCP appengine env variables helper module."""
import functools
import os


@functools.lru_cache
def is_prod() -> bool:
    return os.getenv("GAE_ENV", "") == "standard"


def get_project_id() -> str:
    return os.getenv("GOOGLE_CLOUD_PROJECT", "")
