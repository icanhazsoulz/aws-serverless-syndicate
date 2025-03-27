from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

import json
import os
import boto3
import uuid
from datetime import datetime

_LOG = get_logger(__name__)


class AuditProducer(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        REGION = os.environ['region']
        TABLE_NAME = os.environ['table_name']

        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        audit_table = dynamodb.Table(TABLE_NAME)
        try:
            for record in event['Records']:
                if record['eventName'] not in ['INSERT', 'MODIFY']:
                    continue

                item_key = record['dynamodb']['Keys']['key']['S']

                audit_item = {
                    "id": str(uuid.uuid4()),
                    "itemKey": item_key,
                    "modificationTime": datetime.utcnow().isoformat(timespec='milliseconds') + "Z",
                }

                if record['eventName'] == 'INSERT':
                    new_image = record['dynamodb']['NewImage']
                    audit_item['newValue'] = {
                        'key': new_image['key']['S'],
                        'value': int(new_image['value']['N'])
                    }

                elif record['eventName'] == 'MODIFY':
                    old_value = int(record['dynamodb']['OldImage']['value']['N'])
                    new_value = int(record['dynamodb']['NewImage']['value']['N'])

                    audit_item.update({
                        'oldValue': old_value,
                        'newValue': new_value,
                        'updated_attribute': 'value'
                    })

                audit_table.put_item(Item=audit_item)

            return {
                'statusCode': 200,
                'body': json.dumps('Successfully proceeded {} records'.format(len(event['Records'])))
            }
        except Exception as e:
            _LOG.error(e)
            return {
                'statusCode': 500,
                'body': json.dumps('Failed to proceed {} records'.format(len(event['Records'])))
            }
    

HANDLER = AuditProducer()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
