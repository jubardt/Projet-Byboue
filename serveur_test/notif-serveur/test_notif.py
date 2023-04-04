import onesignal
from onesignal.api import default_api
from onesignal.model.notification import Notification
from onesignal.model.string_map import StringMap

def createNotification():
    notification = Notification()
    notification.set_attribute('app_id', '085aeeea-61e8-4969-989c-373d5765e2d7')
    contentsStringMap = StringMap()   
    contentsStringMap.set_attribute('en', "Gig'em Ags")
    notification.set_attribute('contents', contentsStringMap)
    notification.set_attribute('is_any_web', True)
    #notification.set_attribute('include_player_ids',['b22985b9-6ebe-4ac6-84bd-7f98faca364e'])
    #notification.set_attribute('is_chrome', True)
    notification.set_attribute('included_segments', ['Subscribed Users',"Active Users"])

    return notification

configuration = onesignal.Configuration(
    app_key = "ZGE5OTRmNDktM2E0MC00NDg2LWFjMDItNzY5ZGE1M2RkY2Fh",
    user_key = "085aeeea-61e8-4969-989c-373d5765e2d7"
)


# Enter a context with an instance of the API client
with onesignal.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)
    #notification = Notification() 
    #notification.set_attribute('app_id',"085aeeea-61e8-4969-989c-373d5765e2d7")
    #contentsStringMap = StringMap()
    #contentsStringMap.set_attribute('en', "Loris veut se promener")
    #notification.set_attribute('contents', contentsStringMap)
    #notification.set_attribute('include_player_ids',['ae0b4a5a-ba5f-416d-a071-a54c0aec337e'])
    #notification.set_attribute('is_any_web', True)
    #notification.set_attribute('is_chrome_web', True)

    #notification.set_attribute('included_segments', ['test','Subscribed Users'])

    # example passing only required values which don't have defaults set
    try:
        # Create notification
        notif = createNotification()
        api_response = api_instance.create_notification(notif)
        print(api_response)
    except onesignal.ApiException as e:
        print("Exception when calling DefaultApi->create_notification: %s\n" % e)

