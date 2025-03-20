from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger(__name__)


class HelloWorld(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        """
        Explain incoming event here
        """
        # todo implement business logic
        path = event['path']
        method = event['httpMethod']

        if path == '/hello':
            return {
                "statusCode": 200,
                "message": "Hello from Lambda"
            }
        return {
            "statusCode": 400,
            "message": f"Bad Request syntax or unsupported method. Request path: {path}. HTTP method: {method}"
        }


HANDLER = HelloWorld()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
