from python_framework.config_utils import load_environment_variable
from python_framework.logger import ContextLogger, LogLevel


class SlackIntegration:
    _instance: "SlackIntegration" = None

    _logger_key: str = None

    channel_id: str
    bot_token: str

    def __init__(self, bot_token: str, channel_id: str):
        self._logger_key = "SlackIntegration"

        self.bot_token = bot_token
        self.channel_id = channel_id

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
        )

        return SlackIntegration._instance

    @staticmethod
    def instance() -> "SlackIntegration":
        return SlackIntegration._instance

    def send_message(self, message: str):
        pass

    # TODO: add "send_message" method (http post)
    # curl -X POST \
    #   -H "Content-type: application/json" \
    #   -H "Authorization: Bearer xoxb-your-bot-token" \
    #   -d '{
    #     "channel": "C123456",
    #     "text": "Hello, world!"
    #   }' \
    #   https://slack.com/api/chat.postMessage

    def send_password_reset_message(self, username: str, email: str):
        pass


# TODO: add send_password_reset_message(username)
#       - fixed template
#       - add link to ersilia-hub reset (hub.ersilia.io/#/user-admin?user=username)
#       - use send_message


# ----
# TODO: add forgot_password to user_admin controller
#       - validate username + email (must exist, i.e. do select using BOTH)
#       - call send_password_reset_message
