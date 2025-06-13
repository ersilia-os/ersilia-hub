from base64 import b64decode
from enum import Enum
from json import loads
from typing import Any, Dict, List, Tuple, Union
from fastapi import Request

from re import compile

from pydantic import BaseModel

from objects.user import AuthType, UserModel, UserSession, UserSessionModel

GUEST_USER_PATTERN = compile("(100|(0[0-9]{2}))00000-0000-0000-0000-000000000000")


class TrackingDetails:
    user_agent: str

    def __init__(
        self,
        user_agent: str,
    ):
        self.user_agent = user_agent

    @staticmethod
    def from_request(request: Request) -> "TrackingDetails":
        return TrackingDetails(request.headers.get("User-Agent"))

    def to_object(self) -> Dict[str, Any]:
        return {"user_agent": self.user_agent}

    def __str__(self) -> str:
        return str(self.to_object())

    def __repr__(self) -> str:
        return str(self.to_object())


class AuthDetails:
    auth_type: AuthType
    user_session: UserSession

    def __init__(
        self,
        auth_type: AuthType,
        user_session: UserSession,
    ):
        self.auth_type = auth_type
        self.user_session = user_session

    @staticmethod
    def from_request(request: Request) -> Union[None, "AuthDetails"]:
        auth_header = request.headers.get("Authorization")

        if auth_header is None:
            return None

        auth_type, encoded_header = auth_header.split(" ")

        if auth_type == AuthType.ErsiliaAnonymous or auth_type == AuthType.ErsiliaUser:
            decoded_header = b64decode(encoded_header).decode("ascii")

            return AuthDetails(
                auth_type, UserSession.from_object(loads(decoded_header))
            )

        return None

    def to_object(self) -> Dict[str, Any]:
        return {
            "authType": self.auth_type,
            "userSession": self.user_session.to_object(),
        }

    def __str__(self) -> str:
        return str(self.to_object())

    def __repr__(self) -> str:
        return str(self.to_object())


class EncodedAuthModel(BaseModel):
    encoding: str
    auth_type: AuthType

    def decode_auth_encoding(self) -> Tuple[str, str]:
        if self.auth_type == AuthType.ErsiliaAnonymous:
            # anonymous auth is not encoded
            return self.encoding, None

        elif self.auth_type == AuthType.ErsiliaUser:
            decoded_auth = b64decode(self.encoding).decode("ascii")
            username, password = decoded_auth.split(":")

            if (
                username is None
                or len(username) == 0
                or password is None
                or len(password) < 16
            ):
                raise Exception("Invalid username or password")

            return username, password

        return None, None


class LoginResponseModel(BaseModel):

    session: UserSessionModel
    user: UserModel
    permissions: List[str]
