from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

import json
import uuid
from datetime import datetime
import os
import boto3

_LOG = get_logger(__name__)


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        dynamodb = boto3.resource('dynamodb')
        TABLENAME = 'Events'
        table = dynamodb.Table(TABLENAME)
        try:
            body = json.loads(event['body'])
            principal_id = body.get('principalId')
            content = body.get('content')
            if not principal_id or not content:
                return {"statusCode": 400, "body": json.dumps({"error": "Missing required fields"})}

            event_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()+'Z'

            record = {
                "id": event_id,
                "principalId": principal_id,
                "createdAt": created_at,
                "body": content
            }

            response = table.put_item(Item=record)

            response = {
                "statusCode": 201,
                "body": json.dumps({"event": response})
            }
            return response
        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
