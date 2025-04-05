from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

import json
import os
import boto3
import re
import uuid
from datetime import datetime

_LOG = get_logger(__name__)

cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb', region_name=os.environ['region'])
user_pool_id = os.environ['booking_userpool']
TABLES = os.environ['tables_table']
RESERVATIONS = os.environ['reservations_table']
tables_table = dynamodb.Table(TABLES)
reservations_table = dynamodb.Table(RESERVATIONS)

PASSWORD_REGEX = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[$%^*\-_])[A-Za-z\d$%^*\-_]{12,}$"
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        try:
            body = json.loads(event.get("body", "{}"))
            return body
        except Exception as e:
            _LOG.error(e)

    def handle_signup(self, event):
        body = self.validate_request(event=event)
        if not body:
            return {"statusCode": 400, "body": json.dumps({"message": "Invalid request format"})}

        first_name = body["firstName"].strip()
        last_name = body["lastName"].strip()
        email = body["email"].strip()
        password = body["password"].strip()

        # errors = []
        # if not first_name:
        #     errors.append("First name is required")
        # if not last_name:
        #     errors.append("Last name is required")
        # if not re.fullmatch(EMAIL_REGEX, email):
        #     errors.append("Invalid email format")
        # if not re.fullmatch(PASSWORD_REGEX, password):
        #     errors.append("Password must be 12+ chars with letters, numbers, and symbols ($%^*_-)")
        #
        # if errors:
        #     return {
        #         "statusCode": 400,
        #         "body": json.dumps({"statusCode": 400, "message": "Validation failed", "errors": errors})
        #     }

        if (
            not first_name
            or not last_name
            or not re.fullmatch(EMAIL_REGEX, email)
            or not re.fullmatch(PASSWORD_REGEX, password)
        ):
            return {
                "statusCode": 400,
                "body": json.dumps({"statusCode": 400, "message": "Invalid input data"})
            }

        try:
            cognito_client.sign_up(
                ClientId=cognito_client.client_id, #???
                Username=email,
                Password=password,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "given_name", "Value": first_name},
                    {"Name": "family_name", "Value": last_name},
                ],
            )

            tables_table.put_item(Item={"email": email, "firstName": first_name, "lastName": last_name})
            return {"statusCode": 200, "body": json.dumps({"message": "Sign-up successful"})}
        except Exception as e:
            _LOG.error(f"Sign-up error: {str(e)}")
            return {"statusCode": 400, "body": json.dumps({"message": str(e)})}


    def handle_signin(self, event):
        body = self.validate_request(event=event)
        if not body:
            return {"statusCode": 400, "body": json.dumps({"message": "Invalid request format"})}

        email = body.get("email", "").strip()
        password = body.get("password", "").strip()

        if not email or not password:
            return {"statusCode": 400, "body": json.dumps({"statusCode": 400, "message": "Missing email or password"})}

        try:
            response = cognito_client.initiate_auth(
                ClientId=cognito_client.client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": email, "PASSWORD": password}
            )

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "idToken": response['AuthenticationResult']['IdToken']
                })
            }

        except Exception as e:
            _LOG.error(f"Sign-in error: {str(e)}")
            return {"statusCode": 400, "body": json.dumps({"message": "Invalid credentials"})}

    def handle_list_tables(self, event):
        try:
            # Extract and validate the Authorization header
            auth_header = event.get("headers", {}).get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return {"statusCode": 400, "body": json.dumps({"message": "Missing or invalid token"})}

            # Fetch from DynamoDB
            response = tables_table.scan()
            items = response.get("Items", [])

            # Format tables
            tables = []
            for item in items:
                table = {
                    "id": int(item["id"]),
                    "number": int(item["number"]),
                    "places": int(item["places"]),
                    "isVip": bool(item["isVip"]),
                }
                if "minOrder" in item:
                    table["minOrder"] = int(item["minOrder"])
                tables.append(table)

            return {
                "statusCode": 200,
                "body": json.dumps({"tables": tables})
            }

        except Exception as e:
            _LOG.error(f"Error listing tables: {str(e)}")
            return {"statusCode": 400, "body": json.dumps({"message": "Could not fetch tables"})}

    def handle_create_table(self, event):
        try:
            # Auth check
            auth_header = event.get("headers", {}).get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return {"statusCode": 400, "body": json.dumps({"message": "Missing or invalid token"})}

            # Body parsing
            body = json.loads(event.get("body", "{}"))

            required_fields = ["id", "number", "places", "isVip"]
            if not all(field in body for field in required_fields):
                return {"statusCode": 400, "body": json.dumps({"message": "Missing required fields"})}

            # Build item
            item = {
                "id": int(body["id"]),
                "number": int(body["number"]),
                "places": int(body["places"]),
                "isVip": bool(body["isVip"]),
            }
            if "minOrder" in body:
                item["minOrder"] = int(body["minOrder"])

            # Put to DynamoDB
            tables_table.put_item(Item=item)

            return {
                "statusCode": 200,
                "body": json.dumps({"id": item["id"]})
            }

        except Exception as e:
            _LOG.error(f"Error creating table: {str(e)}")
            return {"statusCode": 400, "body": json.dumps({"message": "Could not create table"})}

    def handle_get_table(self, event):
        try:
            # Auth check
            auth_header = event.get("headers", {}).get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return {"statusCode": 400, "body": json.dumps({"message": "Missing or invalid token"})}

            path_params = event.get("pathParameters", {})
            table_id = path_params.get("tableId")
            if not table_id:
                return {"statusCode": 400, "body": json.dumps({"message": "Missing tableId in path"})}

            # Fetch from DynamoDB
            response = tables_table.get_item(Key={"id": int(table_id)})
            item = response.get("Item")

            if not item:
                return {"statusCode": 400, "body": json.dumps({"message": "Table not found"})}

            # Format response
            table = {
                "id": int(item["id"]),
                "number": int(item["number"]),
                "places": int(item["places"]),
                "isVip": bool(item["isVip"]),
            }
            if "minOrder" in item:
                table["minOrder"] = int(item["minOrder"])

            return {
                "statusCode": 200,
                "body": json.dumps(table)
            }

        except Exception as e:
            _LOG.error(f"Error getting table: {str(e)}")
            return {"statusCode": 400, "body": json.dumps({"message": "Could not get table"})}


    def handle_create_reservation(self, event):
        try:
            auth_header = event.get("headers", {}).get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return {"statusCode": 400, "body": json.dumps({"message": "Missing or invalid token"})}

            body = json.loads(event.get("body", "{}"))

            required_fields = ["tableNumber", "clientName", "phoneNumber", "date", "slotTimeStart", "slotTimeEnd"]
            if not all(field in body for field in required_fields):
                return {"statusCode": 400, "body": json.dumps({"message": "Missing required fields"})}

            # Validate date and time formats
            try:
                datetime.strptime(body["date"], "%Y-%m-%d")
                datetime.strptime(body["slotTimeStart"], "%H:%M")
                datetime.strptime(body["slotTimeEnd"], "%H:%M")
            except ValueError:
                return {"statusCode": 400, "body": json.dumps({"message": "Invalid date or time format"})}

            # Optional: check for overlapping reservations
            table_number = int(body["tableNumber"])
            date = body["date"]
            slot_start = body["slotTimeStart"]
            slot_end = body["slotTimeEnd"]

            existing = dynamodb.Table(os.environ["RESERVATIONS_TABLE"]).scan(
                FilterExpression=(
                        Attr("tableNumber").eq(table_number) &
                        Attr("date").eq(date) &
                        (
                            (Attr("slotTimeStart").lt(slot_end) & Attr("slotTimeEnd").gt(slot_start))
                        )
                )
            )
            if existing.get("Items"):
                return {"statusCode": 400, "body": json.dumps({"message": "Conflicting reservation exists"})}

            # Create reservation
            reservation_id = str(uuid.uuid4())
            item = {
                "reservationId": reservation_id,
                "tableNumber": table_number,
                "clientName": body["clientName"],
                "phoneNumber": body["phoneNumber"],
                "date": date,
                "slotTimeStart": slot_start,
                "slotTimeEnd": slot_end,
            }

            reservations_table.put_item(Item=item)

            return {
                "statusCode": 200,
                "body": json.dumps({"reservationId": reservation_id})
            }

        except Exception as e:
            _LOG.error(f"Error creating reservation: {str(e)}")
            return {"statusCode": 400, "body": json.dumps({"message": "Could not create reservation"})}

    def handle_list_reservations(self, event):
        try:
            auth_header = event.get("headers", {}).get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return {"statusCode": 400, "body": json.dumps({"message": "Missing or invalid token"})}

            # Fetch all reservations
            response = reservations_table.scan()
            items = response.get("Items", [])

            reservations = []
            for item in items:
                reservations.append({
                    "tableNumber": int(item["tableNumber"]),
                    "clientName": item["clientName"],
                    "phoneNumber": item["phoneNumber"],
                    "date": item["date"],
                    "slotTimeStart": item["slotTimeStart"],
                    "slotTimeEnd": item["slotTimeEnd"],
                })

            return {
                "statusCode": 200,
                "body": json.dumps({"reservations": reservations})
            }

        except Exception as e:
            _LOG.error(f"Error listing reservations: {str(e)}")
            return {"statusCode": 400, "body": json.dumps({"message": "Could not fetch reservations"})}

    def handle_request(self, event, context):
        route = event['path'].lower()
        if route.endswith("/signup"):
            return self.handle_signup(event)
        elif route.endswith("/signin"):
            return self.handle_signin(event)
        elif route.endswith("/tables") and event.get("httpMethod") == "GET":
            return self.handle_list_tables(event)
        elif route.endswith("/tables") and event.get("httpMethod") == "POST":
            return self.handle_create_table(event)
        elif route.endswith("/tables") and event.get("httpMethod") == "POST":
            return self.handle_create_table(event)
        elif route.endswith("/tables") and event.get("httpMethod") == "GET":
            return self.handle_list_tables(event)
        elif "/tables/" in route and event.get("httpMethod") == "GET":
            return self.handle_get_table(event)
        elif route.endswith("/reservations") and event.get("httpMethod") == "POST":
            return self.handle_create_reservation(event)
        elif route.endswith("/reservations") and event.get("httpMethod") == "GET":
            return self.handle_list_reservations(event)
        else:
            return {"statusCode": 404, "body": json.dumps({"message": "Resource not found"})}

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
