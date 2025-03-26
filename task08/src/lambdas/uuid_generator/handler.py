from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

import uuid
import json
import boto3
from datetime import datetime
import os

_LOG = get_logger(__name__)


class UuidGenerator(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        s3 = boto3.resource('s3')
        BUCKET_NAME = os.environ['bucket_name']

        try:
            uuid_list = [str(uuid.uuid4()) for _ in range(10)]
            timestamp = datetime.utcnow().isoformat()+'Z'
            filename = f"{timestamp}"

            file_content = json.dumps({"ids": uuid_list}, indent=4)
            s3.put_object(Bucket=BUCKET_NAME, Key=filename, Body=file_content, ContentType='application/json')
            return {"statusCode": 200, "body": "UUID file created successfully"}

        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

HANDLER = UuidGenerator()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
