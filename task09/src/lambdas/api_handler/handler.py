from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

import json
import requests
# from weather_sdk.weather_sdk import OpenMeteoClient

_LOG = get_logger(__name__)


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        URL = 'https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m'
        response = requests.get(URL)
        # return 200
        # client = OpenMeteoClient(URL)
        # response = client.get_current_weather()
        return {
            "statusCode": 200,
            "body": json.dumps(response.json())
        }

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
