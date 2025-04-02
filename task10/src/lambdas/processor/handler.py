from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

import boto3
from datetime import datetime
import json
import os
import requests
import uuid

_LOG = get_logger(__name__)


class Processor(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        URL = 'https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m'

        dynamodb = boto3.resource('dynamodb', region_name=os.environ['region'])
        table = dynamodb.Table(os.environ['table_name'])

        try:
            response = requests.get(URL)
            r = response.json()
            item = {
                "id": str(uuid.uuid4()),
                "forecast": {
                    "elevation": r['elevation'],
                    "generationtime_ms": r['generationtime_ms'],
                    "hourly": {
                        "temperature_2m": r['hourly']['temperature_2m'],
                        "time": r['hourly']['time'],
                    },
                    "hourly_units": {
                        "temperature_2m": r['hourly_units']['temperature_2m'],
                        "time": r['hourly_units']['time'],
                    },
                    "latitude": r['latitude'],
                    "longitude": r['longitude'],
                    "timezone": r['timezone'],
                    "timezone_abbreviation": r['timezone_abbreviation'],
                    "utc_offset_seconds": r['utc_offset_seconds']
                }
            }

            response_meta = table.put_item(Item=item)

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "statusCode": 200,
                    "item": item
                })
            }
        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

HANDLER = Processor()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
