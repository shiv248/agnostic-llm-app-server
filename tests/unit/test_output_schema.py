import unittest

from pydantic import ValidationError
from src.data_classes import OutputSchema

### Unit Test Class for OutputSchema ###

class TestOutputSchema(unittest.TestCase):
    """
    Unit tests for OutputSchema validation.
    This class tests various aspects of OutputSchema such as nested properties,
    valid and invalid type specifications, and general schema structure.
    """

    ### Valid Output Schema Test ###

    def test_output_schema_valid(self):
        """Test a valid OutputSchema with simple properties."""
        valid_output_schema = {
            "type": "object",
            "properties": {
                "sentiment": {"type": "string"}
            }
        }
        schema = OutputSchema(**valid_output_schema)
        self.assertEqual(schema.type, "object")
        self.assertEqual(schema.properties["sentiment"]["type"], "string")

    ### Invalid Type Tests ###

    def test_output_schema_invalid_type(self):
        """Test OutputSchema with an invalid type (e.g., invalid_type instead of object)."""
        invalid_output_schema = {
            "type": "invalid_type",  # Invalid type, should be "object"
            "properties": {
                "sentiment": {"type": "string"}
            }
        }
        with self.assertRaises(ValidationError) as context:
            OutputSchema(**invalid_output_schema)
        # Issue: 'invalid_type' is not 'object'
        self.assertIn("must be 'object'", str(context.exception))

    ### Nested Properties Test ###

    def test_output_schema_with_nested_properties(self):
        """Test OutputSchema with valid nested properties."""
        valid_output_schema = {
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
        schema = OutputSchema(**valid_output_schema)
        self.assertEqual(schema.type, "object")
        self.assertIn("metadata", schema.properties)
        self.assertIn("confidence", schema.properties["metadata"]["properties"])

    ### Invalid Nested Properties Test ###

    def test_output_schema_invalid_nested_property(self):
        """Test OutputSchema with an invalid type inside nested properties."""
        invalid_output_schema = {
            "type": "object",
            "properties": {
                "sentiment": {"type": "string"},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "confidence": {"type": "invalid_type"}  # Invalid type inside nested property
                    }
                }
            }
        }
        with self.assertRaises(ValidationError) as context:
            OutputSchema(**invalid_output_schema)
        # Issue: 'invalid_type' in the nested properties
        self.assertIn("Type 'invalid_type' in properties must be one of", str(context.exception))

    ### Empty Properties Test ###

    def test_output_schema_empty_properties(self):
        """Test OutputSchema where 'properties' is an empty dictionary."""
        invalid_output_schema = {
            "type": "object",
            "properties": {}  # Empty properties
        }
        with self.assertRaises(ValidationError) as context:
            OutputSchema(**invalid_output_schema)
        # Issue: Properties must not be empty
        self.assertIn("Properties must not be empty", str(context.exception))


if __name__ == '__main__':
    unittest.main()
