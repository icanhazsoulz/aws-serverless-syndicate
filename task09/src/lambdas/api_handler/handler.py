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
        http = event['requestContext']['http']
        path = http['path']
        method = http['method']

        URL = 'https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m'
        response = requests.get(URL)

        if path == '/weather':
            return {
                "statusCode": 200,
                "body": json.dumps(response.json())
            }

        return {
            "statusCode": 400,
            "body": json.dumps({
                "statusCode": 400,
                "message": f"Bad Request syntax or unsupported method. Request path: {path}. HTTP method: {method}"
            })
        }

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
