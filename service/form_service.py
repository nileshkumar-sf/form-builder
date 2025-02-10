import logging
from llm.payload_generator import PayloadGenerator
from utils.api_client import ApiClient

class FormService:
    def __init__(self):
        self.payload_generator = PayloadGenerator()
        self.api_client = ApiClient()

    def create_and_trigger_form(self, prompt: str):
        # Generate form based on user prompt
        form_definition = self.payload_generator.generate_form_from_prompt(prompt)
        logging.error(form_definition)
        # Trigger API with the generated form definition (payload)
        response = self.api_client.trigger_api(form_definition)
        return response