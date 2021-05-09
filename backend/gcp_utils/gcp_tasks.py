"""GCP Tasks helper module."""
import datetime
import enum
import importlib
import json
import typing
import os

import pydantic

import grpc
from google.cloud import tasks_v2
from google.cloud.tasks_v2.services.cloud_tasks import (
    transports as tasks_v2_transports,
)
from google.protobuf import timestamp_pb2

from . import gcp_env


TASK_EXEC_HANDLER = "/_internal/safe-and-internal-only-access/task/exec"
_GCP_TASK_HEADERS = frozenset([
    'X-AppEngine-QueueName',
    'X-AppEngine-TaskName',
    'X-AppEngine-TaskRetryCount',
    'X-AppEngine-TaskExecutionCount',
    'X-AppEngine-TaskETA',
])


def _get_cloud_tasks_client() -> tasks_v2.CloudTasksClient:
    kwargs = {}
    if not gcp_env.is_prod():
        channel = grpc.insecure_channel(
            os.getenv("CLOUD_TASKS_EMULATOR_HOST", "")
        )
        kwargs["transport"] = tasks_v2_transports.CloudTasksGrpcTransport(
            channel=channel
        )

    return tasks_v2.CloudTasksClient(**kwargs)


_client = _get_cloud_tasks_client()


class Location(enum.Enum):
    US_CENTRAL1 = "us-central1"
    US-EAST1 = "us-east1"
    DEFAULT = US_CENTRAL1


class Queue(enum.Enum):
    DEFAULT = "default"


class TaskPayload(pydantic.BaseModel):
    module: str
    function: str
    args: typing.List[typing.Any] = pydantic.Field(default_factory=list)
    kwargs: typing.Dict[str, typing.Any] = pydantic.Field(default_factory=dict)


def _create_task(
    payload: TaskPayload,
    deplay: typing.Optional[int] = None,
    location: typing.Optional[Location] = Location.DEFAULT,
    queue: typing.Optional[Queue] = Queue.DEFAULT,
) -> str:
    task = {
        "app_engine_http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "relative_uri": TASK_EXEC_HANDLER,
            "body": json.dumps(payload.dict()).encode(),
            "headers": {"Content-type": "application/json"},
        }
    }
    if deplay:
        utcnow = datetime.datetime.utcnow()
        delta_seconds = datetime.timedelta(seconds=deplay)
        schedule = utcnow + delta_seconds

        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(schedule)
        task["schedule_time"] = timestamp

    parent = _client.queue_path(
        gcp_env.get_project_id(),
        location.value,
        queue.value,
    )
    print(parent)

    response = _client.create_task(parent=parent, task=task)
    return response.name


def defer_execution(
    func: typing.Callable,
    *,
    _delay_in_seconds: typing.Optional[int] = None,
    _task_location: typing.Optional[Location] = Location.DEFAULT,
    _task_queue: typing.Optional[Queue] = Queue.DEFAULT,
    **kwargs,
) -> str:
    payload = TaskPayload(
        module=func.__module__,
        function=func.__name__,
        kwargs=kwargs,
    )
    return _create_task(
        payload,
        deplay=_delay_in_seconds,
        location=_task_location,
        queue=_task_queue,
    )


def exec_task(
    payload: TaskPayload, request_headers: typing.Dict[str, str]
) -> typing.Any:
    # validate request is coming from GCP Tasks
    for gcp_header in _GCP_TASK_HEADERS:
        if gcp_header not in request_headers:
            raise ValueError('Invalid GCP Task request')

    func = getattr(importlib.import_module(payload.module), payload.function)
    return func(**payload.kwargs)
