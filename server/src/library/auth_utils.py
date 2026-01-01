from hashlib import md5
from random import choices, randint
from string import ascii_lowercase, ascii_uppercase, digits

from config.auth_config import AuthConfig
from objects.user import User
from python_framework.time import date_from_string


def generate_password_hash(user: User, password: str) -> str:
    user_datepart = date_from_string(user.sign_up_date).strftime("%Y-%m-%dT%H")
    digest = md5(
        f"{user.username}_{password}_{user_datepart}_{AuthConfig.instance().password_salt}".encode()
    )

    return digest.hexdigest()


def generate_session_token(userid: str) -> str:
    random_token = "".join(choices(ascii_uppercase + digits + ascii_lowercase, k=24))
    digest = md5(f"{userid}_{random_token}".encode())

    return digest.hexdigest()


def get_random_anonymous_userid() -> str:
    anon_user_number = randint(0, AuthConfig.instance().total_anonymous_users)

    return "%s00000-0000-0000-0000-000000000000" % ("%03d" % anon_user_number)
