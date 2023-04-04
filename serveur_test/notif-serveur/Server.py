import onesignal
from onesignal.api import default_api
from onesignal.model.notification import Notification
from onesignal.model.create_notification_success_response import CreateNotificationSuccessResponse
from onesignal.model.bad_request_error import BadRequestError
from pprint import pprint

# See configuration.py for a list of all supported configuration parameters.
# Some of the OneSignal endpoints require USER_KEY bearer token for authorization as long as others require APP_KEY
# (also knows as REST_API_KEY). We recommend adding both of them in the configuration page so that you will not need
# to figure it yourself.
configuration = onesignal.Configuration(
    app_key = "MGEyOTQ2NWQtMjcwNC00NTlhLTlmN2UtYzM2MTg5MDE3ZTAy",
    user_key = "YOUR_USER_KEY"
)


# Enter a context with an instance of the API client
with onesignal.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)
