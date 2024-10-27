import unittest

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestApplicationCreation(unittest.TestCase):

    ### Helper Method ###

    def create_application_request(self, data):
        """Helper method to send a POST request to /applications."""
        return client.post("/applications", json=data)

    ### Valid Request Tests ###

    def test_create_application_valid_request(self):
        """Test the creation of a valid application."""
        valid_data = {
            "prompt_config": "You are an advanced sentiment analysis tool...",
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
        response = self.create_application_request(valid_data)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertIn("application_id", json_response)

    ### Bad Request Tests ###

    def test_create_application_missing_field(self):
        """Test request with missing prompt_config."""
        invalid_data = {
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
        response = self.create_application_request(invalid_data)
        self.assertEqual(response.status_code, 422)
        json_response = response.json()
        self.assertIn("detail", json_response)

    def test_create_application_invalid_input_type(self):
        """Test request where input_schema type is not 'object'."""
        invalid_data = {
            "prompt_config": "You are an advanced sentiment analysis tool...",
            "input_schema": {
                "type": "array",  # Invalid type
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
        response = self.create_application_request(invalid_data)
        self.assertEqual(response.status_code, 422)
        json_response = response.json()
        self.assertIn("detail", json_response)

    def test_create_application_empty_prompt(self):
        """Test request with an empty prompt_config."""
        invalid_data = {
            "prompt_config": "    ",  # Invalid empty string
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
        response = self.create_application_request(invalid_data)
        self.assertEqual(response.status_code, 422)
        json_response = response.json()
        self.assertIn("detail", json_response)

    ### Non-JSON and Invalid Content-Type Tests ###

    def test_create_application_non_json_request(self):
        """Test non-JSON request to the application creation endpoint."""
        response = client.post(
            "/applications",
            content="This is not JSON",
            headers={"Content-Type": "text/plain"}
        )
        self.assertEqual(response.status_code, 422)
        json_response = response.json()
        self.assertIn("detail", json_response)

    ### Multiple Properties ###

    def test_create_application_multiple_properties(self):
        """Test application creation with multiple input/output properties."""
        valid_data = {
            "prompt_config": "Analyze sentiment and extract keywords.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "review_text": {"type": "string"},
                    "author_name": {"type": "string"}
                },
                "required": ["review_text", "author_name"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string"},
                    "keywords": {"type": "array"}
                }
            }
        }
        response = self.create_application_request(valid_data)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertIn("application_id", json_response)

    ### Edge Cases ###

    def test_create_application_no_required_fields(self):
        """Test request with input_schema that has no required fields (should fail)."""
        invalid_data = {
            "prompt_config": "You are an advanced sentiment analysis tool...",
            "input_schema": {
                "type": "object",
                "properties": {
                    "review_text": {"type": "string"}
                }
                # 'required' field is missing, so this should fail validation
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string"}
                }
            }
        }
        response = self.create_application_request(invalid_data)
        self.assertEqual(response.status_code, 422)  # Expecting 422 Unprocessable Entity
        json_response = response.json()
        self.assertIn("detail", json_response)



if __name__ == '__main__':
    unittest.main()
