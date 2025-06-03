from enum import Enum
from typing import Any, Dict, Union

from pydantic import BaseModel
from db.daos.user import UserRecord
from db.daos.user_auth import UserAuthRecord
from db.daos.user_session import UserSessionRecord


class User:
    id: str
    username: str
    first_name: str
    last_name: str
    email: Union[str, None]
    sign_up_date: Union[str, None]
    last_updated: Union[str, None]

    def __init__(
        self,
        id: Union[str, None],
        username: str,
        first_name: str,
        last_name: str,
        email: Union[str, None],
        sign_up_date: Union[str, None] = None,
        last_updated: Union[str, None] = None,
    ):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.sign_up_date = sign_up_date
        self.last_updated = last_updated

    @staticmethod
    def init_from_record(record: UserRecord) -> "User":
        return User(
            record.id,
            record.username,
            record.first_name,
            record.last_name,
            record.email,
            record.sign_up_date,
            record.last_updated,
        )

    def to_record(self) -> UserRecord:
        return UserRecord.init(
            id=self.id,
            username=self.username,
            firstname=self.first_name,
            lastname=self.last_name,
            email=self.email,
            signupdate=self.sign_up_date,
            lastupdated=self.last_updated,
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "signUpDate": self.sign_up_date,
            "lastUpdated": self.last_updated,
        }


class UserModel(BaseModel):

    id: str | None = None
    username: str
    first_name: str
    last_name: str
    email: str | None = None
    sign_up_date: str | None = None
    last_updated: str | None = None

    @staticmethod
    def from_object(user: User) -> "UserModel":
        return UserModel(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            sign_up_date=user.sign_up_date,
            last_updated=user.last_updated,
        )

    def to_object(self) -> User:
        return User(
            self.id,
            self.username,
            self.first_name,
            self.last_name,
            self.email,
            self.sign_up_date,
            self.last_updated,
        )


class UserSignUpModel(BaseModel):

    user: UserModel
    password: str


class AuthType(Enum):

    ErsiliaAnonymous = "ErsiliaAnonymous"
    ErsiliaUser = "ErsiliaUser"

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


class UserAuth:

    userid: str
    password_hash: str

    def __init__(
        self,
        userid: str,
        password_hash: str,
    ):
        self.userid = userid
        self.password_hash = password_hash

    @staticmethod
    def init_from_record(record: UserAuthRecord) -> "UserAuth":
        return UserAuth(
            record.userid,
            record.password_hash,
        )

    def to_record(self) -> UserAuthRecord:
        return UserAuthRecord.init(
            userid=self.userid,
            passwordhash=self.password_hash,
        )


class UserSessionModel(BaseModel):

    userid: str
    session_id: str
    session_token: str
    auth_type: AuthType
    session_max_age_seconds: int
    session_start_time: str | None = None


class UserSession:

    userid: str
    session_id: str
    session_token: str
    auth_type: AuthType
    session_max_age_seconds: int
    session_start_time: Union[str, None]

    def __init__(
        self,
        userid: str,
        session_id: str,
        session_token: str,
        auth_type: AuthType,
        session_max_age_seconds: int,
        session_start_time: Union[str, None] = None,
    ):
        self.userid = userid
        self.session_id = session_id
        self.session_token = session_token
        self.auth_type = auth_type
        self.session_max_age_seconds = session_max_age_seconds
        self.session_start_time = session_start_time

    @staticmethod
    def init_from_record(record: UserSessionRecord) -> "UserSession":
        return UserSession(
            record.userid,
            record.session_id,
            record.session_token,
            record.auth_type,
            record.session_max_age_seconds,
            record.session_start_time,
        )

    def to_record(self) -> UserSessionRecord:
        return UserSessionRecord.init(
            userid=self.userid,
            sessionid=self.session_id,
            sessiontoken=self.session_token,
            authtype=self.auth_type,
            sessionmaxageseconds=self.session_max_age_seconds,
            sessionstarttime=self.session_start_time,
        )

    @staticmethod
    def from_object(obj: Dict[str, Any]) -> "UserSession":
        if obj is None:
            return None

        return UserSession(
            None if "userid" not in obj else obj["userid"],
            None if "session_id" not in obj else obj["session_id"],
            None if "session_token" not in obj else obj["session_token"],
            None if "auth_type" not in obj else obj["auth_type"],
            (
                None
                if "session_max_age_seconds" not in obj
                else obj["session_max_age_seconds"]
            ),
            None if "session_start_time" not in obj else obj["session_start_time"],
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "userid": self.userid,
            "session_id": self.session_id,
            "session_token": self.session_token,
            "auth_type": self.auth_type,
            "session_max_age_seconds": self.session_max_age_seconds,
            "session_start_time": self.session_start_time,
        }

    def to_model(self) -> UserSessionModel:
        return UserSessionModel(
            userid=self.userid,
            session_id=self.session_id,
            session_token=self.session_token,
            auth_type=self.auth_type,
            session_max_age_seconds=self.session_max_age_seconds,
            session_start_time=self.session_start_time,
        )
