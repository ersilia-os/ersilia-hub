from enum import Enum
from typing import List, Union

from pydantic import BaseModel
from db.daos.user_permission import UserPermissionRecord
from json import dumps, loads


class Permission(Enum):

    ADMIN = "ADMIN"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        elif self.__class__ is other.__class__:
            return self.value == other.value

        return self.value == other

    def __str__(self):
        return self.name

    def __hash__(self):
        return str(self.name).__hash__()


class UserPermission:

    userid: str
    permissions: List[str]
    last_updated: Union[str, None]

    def __init__(
        self,
        userid: str,
        permissions: List[str],
        last_updated: Union[str, None] = None,
    ):
        self.userid = userid
        self.permissions = permissions
        self.last_updated = last_updated

    @staticmethod
    def init_from_record(record: UserPermissionRecord) -> "UserPermission":
        return UserPermission(
            record.userid,
            loads(record.permissions),
            record.last_updated,
        )

    def to_record(self) -> UserPermissionRecord:
        return UserPermissionRecord.init(
            userid=self.userid,
            permissions=dumps(self.permissions),
            lastupdated=self.last_updated,
        )

    def to_model(self) -> "UserPermissionModel":
        return UserPermissionModel(
            userid=self.userid,
            permissions=self.permissions,
            last_updated=self.last_updated,
        )


class UserPermissionModel(BaseModel):

    userid: str
    permissions: List[str]
    last_updated: str | None = None

    @staticmethod
    def from_object(obj: UserPermission) -> "UserPermissionModel":
        return UserPermissionModel(
            userid=obj.userid,
            permissions=obj.permissions,
            last_updated=obj.last_updated,
        )
