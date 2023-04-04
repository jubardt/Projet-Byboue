from flask import Flask
from flask_restful import Api, Resource
from flask_cors import CORS
import onesignal
from onesignal.api import default_api
from onesignal.model.notification import Notification
from onesignal.model.string_map import StringMap

app = Flask(__name__)
CORS(app)
api = Api(app)

class NotifAPI(Resource):
    def get(self):
        print("Requete OK")
        sendNotification()
        

    

def createNotification():
    notification = Notification()
    notification.set_attribute('app_id', '085aeeea-61e8-4969-989c-373d5765e2d7')
    contentsStringMap = StringMap()   
    contentsStringMap.set_attribute('en', "Gig'em Ags")
    notification.set_attribute('contents', contentsStringMap)
    #notification.set_attribute('is_any_web', True)
    notification.set_attribute('include_player_ids',['9f7fab00-322e-43a4-bb9b-4102027b3660'])
    #notification.set_attribute('is_chrome', True)
    notification.set_attribute('included_segments', ['Subscribed Users'])

    return notification

def sendNotification():
    # Enter a context with an instance of the API client
    configuration = onesignal.Configuration(
        app_key = "ZGE5OTRmNDktM2E0MC00NDg2LWFjMDItNzY5ZGE1M2RkY2Fh",
        api_key = "ZGE5OTRmNDktM2E0MC00NDg2LWFjMDItNzY5ZGE1M2RkY2Fh",
        user_key = "085aeeea-61e8-4969-989c-373d5765e2d7"
    )

    with onesignal.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = default_api.DefaultApi(api_client)
        try:
            # Create notification
            notif = createNotification()
            api_response = api_instance.create_notification(notif)
            print(api_response)
            return api_response
        except onesignal.ApiException as e:
            print("Exception when calling DefaultApi->create_notification: %s\n" % e)
            print("Error")


api.add_resource(NotifAPI,'/sendNotif',endpoint="sendNotif")

if __name__ == '__main__':
    app.run(debug=True)