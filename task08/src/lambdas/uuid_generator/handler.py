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
        try:
            uuids = [str(uuid.uuid4()) for _ in range(10)]
            data = {"ids": uuids}
            json_data = json.dumps(data, indent=4)

            filename = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'

            s3 = boto3.client('s3')
            BUCKET_NAME = os.environ['bucket_name']
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=filename,
                Body=json_data
            )

            return {"statusCode": 200, "body": json.dumps({"UUID file created successfully"})}

        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

HANDLER = UuidGenerator()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
