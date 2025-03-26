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
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['region'])
        TABLE_NAME = os.environ['table_name']
        table = dynamodb.Table(TABLE_NAME)

        try:
            body = json.loads(event['body'])
            principal_id = body['principalId']
            content = body['content']
            if not principal_id or not content:
                return {"statusCode": 400, "body": json.dumps({"error": "Missing required fields"})}

            item = {
                "id": str(uuid.uuid4()),
                "principalId": principal_id,
                "createdAt": datetime.utcnow().isoformat()+'Z',
                "body": content
            }

            response = table.put_item(Item=item)

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
