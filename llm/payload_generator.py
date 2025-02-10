import logging
import json
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

class PayloadGenerator:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )

        # Define a prompt template to instruct the LLM
        self.prompt_template = PromptTemplate(
            input_variables=["user_description"],
            template="""You are a helpful assistant that generates form structures based on user descriptions.
            Your response must be a valid JSON object and nothing else - no explanations or additional text.
            Generate a JSON form template based on this request: {user_description}

            Requirements:
            1. Follow the exact schema structure below
            2. Field types must be one of: ['text', 'text_area', 'currency', 'dropdown', 'radio', 'checkbox']
            3. Each field must have proper validations
            4. Generate meaningful descriptions for form, sections, and fields
            5. IMPORTANT: Each section must have a unique refKey (e.g., "section_1", "personal_info", etc.)
            6. IMPORTANT: Each field's refKey must match its parent section's refKey to create the link
            7. Use logical sequences for sections and fields

            Schema template with example refKey linking:
            {{
                "form": {{
                    "name": "string",
                    "description": "string",
                    "status": "draft",
                    "type": "bpmnusertask"
                }},
                "formVersion": {{
                    "formId": "string",
                    "version": 1,
                    "formGroups": [
                        {{
                            "name": "Personal Information",
                            "description": "Basic personal details",
                            "sequence": 1,
                            "type": "section",
                            "refKey": "personal_info",
                            "configurations": {{
                                "basicConfig": {{
                                    "label": "Personal Information",
                                    "hidelabel": false,
                                    "hidefield": false,
                                    "collapseUi": false,
                                    "byDefaultOpen": true
                                }},
                                "layout": {{
                                    "column": 1,
                                    "sectionKey": "personal_info"
                                }}
                            }},
                            "fields": [
                                {{
                                    "fieldTypeId": "name_field",
                                    "name": "Full Name",
                                    "description": "Enter your full name",
                                    "configurations": {{
                                        "basicConfig": {{
                                            "label": "Full Name",
                                            "placeholder": "John Doe",
                                            "key": "full_name"
                                        }},
                                        "validations": {{
                                            "required": "yes",
                                            "reqErrorMsg": "Name is required",
                                            "valueType": "string",
                                            "min": 2,
                                            "max": 100
                                        }},
                                        "layout": {{
                                            "column": 1,
                                            "ref_key": "personal_info"
                                        }}
                                    }},
                                    "sequence": 1,
                                    "fieldType": "text",
                                    "refKey": "personal_info"
                                }}
                            ]
                        }}
                    ]
                }}
            }}

            Return only valid JSON without any additional text or explanations."""
        )

        # Create the chain using LLM and PromptTemplate
        self.chain = self.prompt_template | self.llm | JsonOutputParser()

    def generate_form_from_prompt(self, prompt: str) -> dict:
        """
        Takes a user prompt and generates a structured form definition.

        Args:
            prompt (str): User description of the desired form

        Returns:
            dict: A dictionary containing the form definition

        Raises:
            json.JSONDecodeError: If the LLM response cannot be parsed as JSON
            ValueError: If the response structure is invalid
        """
        try:
            # Get the response from the LLM
            response = self.chain.invoke({"user_description": prompt})

            # Validate the structure
            self._validate_form_structure(response)

            logging.info(f"Generated form definition: {response}")
            return response

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON. Response: {response}")
            raise
        except ValueError as e:
            logging.error(f"Invalid response structure: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Error generating form: {str(e)}")
            raise

    def _validate_form_structure(self, form_definition: dict):
        """
        Validates the form definition structure including refKey relationships.

        Args:
            form_definition (dict): The form definition to validate

        Raises:
            ValueError: If the structure is invalid
        """
        if not isinstance(form_definition, dict):
            raise ValueError("Response must be a JSON object")

        required_keys = ["form", "formVersion"]
        for key in required_keys:
            if key not in form_definition:
                raise ValueError(f"Response must contain '{key}' field")

        if "formGroups" not in form_definition["formVersion"]:
            raise ValueError("formVersion must contain 'formGroups' array")

        # Collect all section refKeys
        section_ref_keys = set()
        for group in form_definition["formVersion"]["formGroups"]:
            if "refKey" not in group:
                raise ValueError(f"Section '{group.get('name', 'unnamed')}' missing refKey")
            section_ref_keys.add(group["refKey"])

            if "fields" not in group:
                raise ValueError("Each formGroup must contain 'fields' array")

            valid_field_types = ['text', 'text_area', 'currency', 'dropdown', 'radio', 'checkbox']
            for field in group["fields"]:
                # Validate field type
                if field["fieldType"] not in valid_field_types:
                    raise ValueError(f"Invalid field type: {field['fieldType']}")

                # Validate field refKey matches section
                if "refKey" not in field:
                    raise ValueError(f"Field '{field.get('name', 'unnamed')}' missing refKey")
                if field["refKey"] != group["refKey"]:
                    raise ValueError(
                        f"Field '{field.get('name', 'unnamed')}' has refKey '{field['refKey']}' "
                        f"that doesn't match its section refKey '{group['refKey']}'"
                    )

            # Validate section configuration
            if "configurations" in group and "layout" in group["configurations"]:
                if group["configurations"]["layout"].get("sectionKey") != group["refKey"]:
                    raise ValueError(
                        f"Section '{group.get('name', 'unnamed')}' has mismatched "
                        f"sectionKey in layout configuration"
                    )
