import os
import requests

class ApiClient:
    def __init__(self):
        self.api_url = os.getenv('FORM_API_BASE_URL')

    def trigger_api(self, payload: dict):
        # Call external API with generated payload
        token  = 'Bearer ' + os.getenv('FORM_API_TOKEN')
        response = requests.post(self.api_url + '/forms', json=payload, headers={"Authorization": token})
        return response.json()
