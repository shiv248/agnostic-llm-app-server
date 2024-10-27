import unittest

from src.data_classes import ApplicationCreateRequest, validate_input_against_schema, validate_output_against_schema, \
    validate_app_construct_input


class TestValidationFunctions(unittest.TestCase):
    """
    Unit tests for validation functions in the LLM Application Server, covering schema validation
    for input and output as well as application construction requests.
    """

    def test_validate_input_against_schema_valid(self):
        """Test validate_input_against_schema with valid input that matches schema."""
        schema_data = {
            "type": "object",
            "properties": {
                "review_text": {"type": "string"},
                "rating": {"type": "number"}
            },
            "required": ["review_text"]
        }
        input_data = {
            "review_text": "Great product!",
            "rating": 4.5
        }
        errors = validate_input_against_schema(input_data, schema_data)
        self.assertIsNone(errors)

    def test_validate_input_against_schema_missing_required(self):
        """Test validate_input_against_schema with missing required field 'review_text'."""
        schema_data = {
            "type": "object",
            "properties": {
                "review_text": {"type": "string"}
            },
            "required": ["review_text"]
        }
        input_data = {}  # Missing 'review_text'
        errors = validate_input_against_schema(input_data, schema_data)
        self.assertIn("Missing required field: 'review_text'", errors)

    def test_validate_input_against_schema_unexpected_field(self):
        """Test validate_input_against_schema with an unexpected field 'extra_field' in input."""
        schema_data = {
            "type": "object",
            "properties": {
                "review_text": {"type": "string"}
            },
            "required": ["review_text"]
        }
        input_data = {
            "review_text": "Excellent service!",
            "extra_field": "unexpected"  # Unexpected field
        }
        errors = validate_input_against_schema(input_data, schema_data)
        self.assertIn("Unexpected field 'extra_field' in input data.", errors)

    def test_validate_input_against_schema_invalid_type(self):
        """Test validate_input_against_schema with an invalid type for 'rating' (should be number)."""
        schema_data = {
            "type": "object",
            "properties": {
                "review_text": {"type": "string"},
                "rating": {"type": "number"}
            },
            "required": ["review_text"]
        }
        input_data = {
            "review_text": "Excellent service!",
            "rating": "five"  # Invalid type, should be a number
        }
        errors = validate_input_against_schema(input_data, schema_data)
        self.assertIn("Field 'rating' should be of type 'number'.", errors)

    def test_validate_app_construct_input_valid(self):
        """Test validate_app_construct_input with valid request data."""
        request_data = {
            "prompt_config": "Config for prompt",
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
                    "summary": {"type": "string"}
                }
            }
        }
        errors, validated_schema = validate_app_construct_input(request_data)
        self.assertIsNone(errors)
        self.assertIsInstance(validated_schema, ApplicationCreateRequest)

    def test_validate_app_construct_input_missing_field(self):
        """Test validate_app_construct_input with missing 'prompt_config' field."""
        request_data = {
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
                    "summary": {"type": "string"}
                }
            }
        }
        errors, validated_schema = validate_app_construct_input(request_data)
        self.assertIsNotNone(errors)
        self.assertIsNone(validated_schema)
        self.assertEqual(errors["msg"], "Missing required field: 'prompt_config'")

    def test_validate_app_construct_input_invalid_input_schema(self):
        """Test validate_app_construct_input with invalid 'type' in input_schema properties."""
        request_data = {
            "prompt_config": "Valid config",
            "input_schema": {
                "type": "object",
                "properties": {
                    "review_text": {"type": 12345}  # Invalid type, should be a string
                },
                "required": ["review_text"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"}
                }
            }
        }
        errors, validated_schema = validate_app_construct_input(request_data)
        self.assertIsNotNone(errors)
        self.assertIsNone(validated_schema)
        self.assertTrue(any("Each 'type' in properties must be a string" in error["msg"] for error in errors))

    def test_validate_app_construct_input_empty_properties(self):
        """Test validate_app_construct_input with empty properties in input_schema."""
        request_data = {
            "prompt_config": "Valid config",
            "input_schema": {
                "type": "object",
                "properties": {},  # Empty properties
                "required": ["some_field"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"}
                }
            }
        }
        errors, validated_schema = validate_app_construct_input(request_data)
        self.assertIsNotNone(errors)
        self.assertIsNone(validated_schema)
        self.assertTrue(
            any("Properties must be defined before specifying required fields." in error["msg"] for error in errors))

    def test_validate_output_against_schema_valid(self):
        """Test validate_output_against_schema with valid output that matches schema."""
        schema_data = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "score": {"type": "number"}
            }
        }
        output_data = {
            "summary": "This is a great product.",
            "score": 4.5
        }
        errors = validate_output_against_schema(output_data, schema_data)
        self.assertIsNone(errors)

    def test_validate_output_against_schema_missing_field(self):
        """Test validate_output_against_schema with a missing 'score' field specified in schema."""
        schema_data = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "score": {"type": "number"}
            }
        }
        output_data = {
            "summary": "This is a great product."
            # Missing 'score' field
        }
        errors = validate_output_against_schema(output_data, schema_data)
        self.assertIsNone(errors)  # No required fields specified, so should pass

    def test_validate_output_against_schema_unexpected_field(self):
        """Test validate_output_against_schema with an unexpected 'extra_field' in output."""
        schema_data = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"}
            }
        }
        output_data = {
            "summary": "Excellent product!",
            "extra_field": "unexpected"  # Unexpected field
        }
        errors = validate_output_against_schema(output_data, schema_data)
        self.assertIn("Unexpected field 'extra_field' in output data.", errors)

    def test_validate_output_against_schema_invalid_type(self):
        """Test validate_output_against_schema with an invalid 'score' type (should be number)."""
        schema_data = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "score": {"type": "number"}
            }
        }
        output_data = {
            "summary": "Excellent product!",
            "score": "high"  # Invalid type, should be a number
        }
        errors = validate_output_against_schema(output_data, schema_data)
        self.assertIn("Field 'score' should be of type 'number'.", errors)

    def test_validate_output_against_schema_empty_properties(self):
        """Test validate_output_against_schema with an empty properties schema."""
        schema_data = {
            "type": "object",
            "properties": {}  # Empty properties
        }
        output_data = {
            "summary": "Unexpected field in empty properties."
        }
        errors = validate_output_against_schema(output_data, schema_data)
        self.assertIn("Properties must not be empty.", errors[0])

    def test_validate_output_against_schema_nested_properties(self):
        """Test validate_output_against_schema with nested properties in 'details' object."""
        schema_data = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "details": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "number"},
                        "comment": {"type": "string"}
                    }
                }
            }
        }
        output_data = {
            "summary": "Great product",
            "details": {
                "score": 4.5,
                "comment": "Very satisfied"
            }
        }
        errors = validate_output_against_schema(output_data, schema_data)
        self.assertIsNone(errors)


if __name__ == '__main__':
    unittest.main()
