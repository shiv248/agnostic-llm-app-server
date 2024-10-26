import unittest
from pydantic import ValidationError
from src.data_classes import InputSchema


class TestInputSchema(unittest.TestCase):
    """
    Unit tests for InputSchema validation.
    This class covers different cases for validating the InputSchema including
    valid schemas, invalid types, missing required fields, and nested structures.
    """

    def test_input_schema_valid(self):
        """Test a valid InputSchema with multiple properties and required fields."""
        valid_input_schema = {
            "type": "object",
            "properties": {
                "review_text": {"type": "string"},
            },
            "required": ["review_text"]
        }
        schema = InputSchema(**valid_input_schema)
        self.assertEqual(schema.type, "object")
        self.assertEqual(schema.properties["review_text"]["type"], "string")
        self.assertIn("review_text", schema.required)

    def test_input_schema_invalid_type(self):
        """Test InputSchema with an invalid type ('array' instead of 'object')."""
        invalid_input_schema = {
            "type": "array",  # Invalid type, should be "object"
            "properties": {
                "review_text": {"type": "string"}
            },
            "required": ["review_text"]
        }
        with self.assertRaises(ValidationError) as context:
            InputSchema(**invalid_input_schema)
        # Issue: "type" is 'array', but must be 'object'
        self.assertIn("The schema 'type' must be 'object'", str(context.exception))

    def test_input_schema_missing_required_field_in_properties(self):
        """Test InputSchema where a required field is not defined in properties."""
        invalid_input_schema = {
            "type": "object",
            "properties": {
                "review_text": {"type": "string"}
            },
            "required": ["nonexistent_field"]  # Field is not defined in properties
        }
        with self.assertRaises(ValidationError) as context:
            InputSchema(**invalid_input_schema)
        # Issue: "nonexistent_field" is in required but not in properties
        self.assertIn("Required field 'nonexistent_field' is not defined in properties", str(context.exception))

    def test_input_schema_properties_not_defined_before_required(self):
        """Test InputSchema with missing properties but required fields are specified."""
        invalid_input_schema = {
            "type": "object",
            "required": ["review_text"]  # Properties must be defined before required
        }
        with self.assertRaises(ValidationError) as context:
            InputSchema(**invalid_input_schema)
        # Issue: Required fields are specified, but properties are missing
        self.assertIn("Properties must be defined before specifying required fields.", str(context.exception))

    def test_input_schema_with_multiple_properties(self):
        """Test InputSchema with multiple properties and multiple required fields."""
        valid_input_schema = {
            "type": "object",
            "properties": {
                "review_text": {"type": "string"},
                "rating": {"type": "integer"},
                "metadata": {"type": "object"}
            },
            "required": ["review_text", "rating"]
        }
        schema = InputSchema(**valid_input_schema)
        self.assertEqual(schema.type, "object")
        self.assertIn("review_text", schema.properties)
        self.assertIn("rating", schema.properties)
        self.assertIn("review_text", schema.required)
        self.assertIn("rating", schema.required)

    def test_input_schema_with_nested_properties(self):
        """Test InputSchema with nested properties (object inside object)."""
        valid_input_schema = {
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
        }
        schema = InputSchema(**valid_input_schema)
        self.assertEqual(schema.type, "object")
        self.assertIn("author", schema.properties)
        self.assertIn("name", schema.properties["author"]["properties"])

    def test_input_schema_invalid_properties_type(self):
        """Test InputSchema with invalid type for properties fields (e.g., integer instead of string)."""
        invalid_input_schema = {
            "type": "object",
            "properties": {
                "review_text": {"type": 12345}  # Invalid type, should be "string"
            },
            "required": ["review_text"]
        }
        with self.assertRaises(ValidationError) as context:
            InputSchema(**invalid_input_schema)
        
        # Update the assertion to check for the correct error message
        self.assertIn("Each 'type' in properties must be a string", str(context.exception))


    def test_input_schema_empty_properties_has_req(self):
        """Test InputSchema where 'properties' is an empty dictionary but required is defined"""
        invalid_input_schema = {
            "type": "object",
            "properties": {},  # Empty properties
            "required": ["some_field"]
        }
        with self.assertRaises(ValidationError) as context:
            InputSchema(**invalid_input_schema)

        # Updated assertions to match the actual error message
        self.assertIn("Properties must be defined before specifying required fields", str(context.exception))
        self.assertIn("Value error", str(context.exception))


    def test_input_schema_no_properties_has_req(self):
        """Test InputSchema where 'properties' is not defined but required is defined."""
        invalid_input_schema = {
            "type": "object",
            "required": ["some_field"]
        }
        with self.assertRaises(ValidationError) as context:
            InputSchema(**invalid_input_schema)
        # Issue: Properties must exist if required fields exist
        self.assertIn("Properties must be defined before specifying required fields", str(context.exception))


if __name__ == '__main__':
    unittest.main()
