import unittest

from pydantic import ValidationError
from src.data_classes import ApplicationCreateRequest

### Unit Test Class for ApplicationCreateRequest ###

class TestApplicationCreateRequest(unittest.TestCase):
    """
    Unit tests for ApplicationCreateRequest validation.
    This class covers different cases for validating the ApplicationCreateRequest,
    such as valid requests, empty or whitespace prompt_config, and nested schemas.
    """

    ### Valid Request Test ###

    def test_application_create_request_valid(self):
        """Test a valid ApplicationCreateRequest with both input and output schemas."""
        valid_application_request = {
            "prompt_config": "You are an advanced sentiment analysis tool.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "review_text": {"type": "string"}
                },
                "required": ["review_text"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string"}
                }
            }
        }
        app_request = ApplicationCreateRequest(**valid_application_request)
        self.assertEqual(app_request.prompt_config, "You are an advanced sentiment analysis tool.")

    ### Invalid Prompt Config Tests ###

    def test_application_create_request_empty_prompt_config(self):
        """Test ApplicationCreateRequest with an empty prompt_config (should raise validation error)."""
        invalid_application_request = {
            "prompt_config": "", # invalid prompt empty
            "input_schema": {
                "type": "object",
                "properties": {
                    "review_text": {"type": "string"}
                },
                "required": ["review_text"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string"}
                }
            }
        }
        with self.assertRaises(ValidationError) as context:
            ApplicationCreateRequest(**invalid_application_request)
        self.assertIn("Prompt configuration cannot be empty", str(context.exception))

    def test_application_create_request_whitespace_prompt_config(self):
        """Test ApplicationCreateRequest with a prompt_config that only contains whitespace."""
        invalid_application_request = {
            "prompt_config": "   ",  # Only whitespace
            "input_schema": {
                "type": "object",
                "properties": {
                    "review_text": {"type": "string"}
                },
                "required": ["review_text"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string"}
                }
            }
        }
        with self.assertRaises(ValidationError) as context:
            ApplicationCreateRequest(**invalid_application_request)
        self.assertIn("Prompt configuration cannot be empty", str(context.exception))

    ### Invalid Schema Type Tests ###

    def test_application_create_request_invalid_input_schema(self):
        """Test ApplicationCreateRequest with an invalid input schema (wrong type)."""
        invalid_application_request = {
            "prompt_config": "You are an advanced sentiment analysis tool.",
            "input_schema": {
                "type": "invalid_type",  # Invalid type for input schema
                "properties": {
                    "review_text": {"type": "string"}
                },
                "required": ["review_text"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string"}
                }
            }
        }
        with self.assertRaises(ValidationError) as context:
            ApplicationCreateRequest(**invalid_application_request)
        self.assertIn("must be 'object'", str(context.exception))

    def test_application_create_request_invalid_output_schema(self):
        """Test ApplicationCreateRequest with an invalid output schema."""
        invalid_application_request = {
            "prompt_config": "You are an advanced sentiment analysis tool.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "review_text": {"type": "string"}
                },
                "required": ["review_text"]
            },
            "output_schema": {
                "type": "invalid_type",  # Invalid type for output schema
                "properties": {
                    "sentiment": {"type": "string"}
                }
            }
        }
        with self.assertRaises(ValidationError) as context:
            ApplicationCreateRequest(**invalid_application_request)
        self.assertIn("must be 'object'", str(context.exception))

    ### Complex Schema Test ###

    def test_application_create_request_with_complex_nested_schemas(self):
        """Test ApplicationCreateRequest with valid complex nested input and output schemas."""
        valid_application_request = {
            "prompt_config": "You are an advanced sentiment analysis tool.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "review_text": {"type": "string"},
                    "author": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string"}
                        },
                        "required": ["name"]
                    }
                },
                "required": ["review_text"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string"},
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "confidence": {"type": "number"},
                            "source": {"type": "string"}
                        }
                    }
                }
            }
        }
        app_request = ApplicationCreateRequest(**valid_application_request)
        self.assertEqual(app_request.prompt_config, "You are an advanced sentiment analysis tool.")
        self.assertIn("author", app_request.input_schema.properties)
        self.assertIn("metadata", app_request.output_schema.properties)


if __name__ == '__main__':
    unittest.main()
