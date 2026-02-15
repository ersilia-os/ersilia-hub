from sys import exc_info
from time import sleep

from python_framework.config_utils import load_environment_variable
from python_framework.logger import ContextLogger, LogLevel
from requests import post

SLACK_MSG_TEMPLATE_PASSWORD_RESET = """
Password reset requested by user [`%(username)s`] with email [<mailto:%(email)s|%(email)s>].

<%(link)s|Reset password link>
"""


class SlackIntegration:
    _instance: "SlackIntegration" = None

    _logger_key: str = None

    bot_token: str
    channel_id: str
    slack_base_url: str

    def __init__(self, bot_token: str, channel_id: str, slack_base_url: str):
        self._logger_key = "SlackIntegration"

        self.bot_token = bot_token
        self.channel_id = channel_id
        self.slack_base_url = slack_base_url

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "SlackIntegration":
        if SlackIntegration._instance is not None:
            return SlackIntegration._instance

        SlackIntegration._instance = SlackIntegration(
            load_environment_variable("SLACK_TOKEN", error_on_none=True),
            load_environment_variable("SLACK_CHANNEL_ID", error_on_none=True),
            load_environment_variable(
                "SLACK_BASE_URL", default="https://slack.com/api"
            ),
        )

        return SlackIntegration._instance

    @staticmethod
    def instance() -> "SlackIntegration":
        return SlackIntegration._instance

    def send_text_message(self, channel_id: str, message: str) -> bool:
        try:
            response = post(
                url=f"{self.slack_base_url}/chat.postMessage",
                json={
                    "channel": channel_id,
                    "text": message,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.bot_token}",
                },
                timeout=30,
            )
            response.raise_for_status()

            ContextLogger.debug(
                self._logger_key, "Slack Message successfully sent:\n%s" % message
            )

            return True
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to send Slack message, error = [%s]" % repr(exc_info()),
            )

            return False

    def send_password_reset_message(self, username: str, email: str) -> bool:
        message = SLACK_MSG_TEMPLATE_PASSWORD_RESET % {
            "username": username,
            "email": email,
            "link": f"https://hub.ersilia.io/users?username={username}",
        }

        warn_log_message = f"Failed to send password reset message for username [{username}] and email [{email}]."

        if not self.send_text_message(self.channel_id, message):
            ContextLogger.warn(
                self._logger_key, f"{warn_log_message} Retrying once in 5s..."
            )

            sleep(5)

            if not self.send_text_message(self.channel_id, message):
                ContextLogger.error(
                    self._logger_key, f"{warn_log_message} Not retrying again."
                )

                return False

        ContextLogger.info(
            self._logger_key,
            f"Password reset message sent for username [{username}] and email [{email}]",
        )

        return True
