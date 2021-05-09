from __future__ import annotations

import datetime
import uuid
import typing

import pydantic

from google.cloud import ndb


class ItemNdb(ndb.Model):
    # id: uuid4
    TID = uuid.UUID
    name: str = ndb.StringProperty(required=True)
    price: float = ndb.FloatProperty(required=True)
    is_offer: typing.Optional[bool] = ndb.BooleanProperty(required=False)
    created_at: typing.Optional[datetime.datetime] = ndb.DateTimeProperty(
        auto_now_add=True
    )

    @classmethod
    def generate_id(cls) -> str:
        return str(uuid.uuid4())

    @classmethod
    def get_by_id(cls, id_, *args, **kwargs) -> ItemNdb:
        return super().get_by_id(str(id_), *args, **kwargs)


class ItemCreatePyd(pydantic.BaseModel):
    name: str
    price: pydantic.PositiveFloat
    is_offer: typing.Optional[bool] = False


class ItemDetailPyd(ItemCreatePyd):
    id: ItemNdb.TID
    created_at: datetime.datetime

    @classmethod
    def load_from_ndb(cls, item: ItemNdb) -> typing.List[ItemDetailPyd]:
        return ItemDetailPyd(id=item.key.id(), **item.to_dict())


class ItemFiltersPyd(pydantic.BaseModel):
    name_startswith: typing.Optional[str]
    is_offer: typing.Optional[bool]
    min_price: typing.Optional[float]
    max_price: typing.Optional[float]
