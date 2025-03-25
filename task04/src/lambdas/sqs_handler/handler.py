from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
import json
import logging

_LOG = get_logger(__name__)


class SqsHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        """
        Explain incoming event here
        """
        logger = get_logger(__name__)
        logger.setLevel(logging.INFO)
        for record in event['Records']:
            message = record['body']
            logger.info(message)
        return {"statusCode": 200, "body": "SQS message processed successfully"}
    

HANDLER = SqsHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
