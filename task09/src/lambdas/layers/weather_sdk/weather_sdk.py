import requests

class OpenMeteoClient:

    def __init__(self, url):
        # self.url = url
        pass

    def get_current_weather(self):
        """Fetch current weather conditions from OpenMeteo"""
        # response = requests.get(self.url)
        # return {'statusCode': 200, 'body': response.json()} if response.status_code == 200 else {"error": "Failed to fetch data."}