"""GCP appengine env variables helper module."""
import os


def is_prod() -> bool:
    return os.getenv("SERVER_SOFTWARE", "").startswith("Google App Engine/")


def get_project_id() -> str:
    return os.getenv("GOOGLE_CLOUD_PROJECT", "")
