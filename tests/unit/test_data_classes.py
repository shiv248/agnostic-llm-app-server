# import unittest
# from pydantic import ValidationError
# from src.data_classes import InputSchema, OutputSchema, ApplicationCreateRequest
#
# class TestInputSchema(unittest.TestCase):
#
#     def test_input_schema_valid(self):
#         """Test a valid InputSchema."""
#         valid_input_schema = {
#             "type": "object",
#             "properties": {
#                 "review_text": {"type": "string"},
#                 "rating": {"type": "integer"}
#             },
#             "required": ["review_text"]
#         }
#         schema = InputSchema(**valid_input_schema)
#         self.assertEqual(schema.type, "object")
#         self.assertEqual(schema.properties["review_text"]["type"], "string")
#         self.assertIn("review_text", schema.required)
#
#     def test_input_schema_invalid_type(self):
#         """Test InputSchema with an invalid type."""
#         invalid_input_schema = {
#             "type": "array",  # Invalid type, should be "object"
#             "properties": {
#                 "review_text": {"type": "string"}
#             },
#             "required": ["review_text"]
#         }
#         with self.assertRaises(ValidationError) as context:
#             InputSchema(**invalid_input_schema)
#         self.assertIn("must be 'object'", str(context.exception))
#
#     def test_input_schema_missing_required_field_in_properties(self):
#         """Test InputSchema where a required field is not in properties."""
#         invalid_input_schema = {
#             "type": "object",
#             "properties": {
#                 "review_text": {"type": "string"}
#             },
#             "required": ["nonexistent_field"]  # Field is not defined in properties
#         }
#         with self.assertRaises(ValidationError) as context:
#             InputSchema(**invalid_input_schema)
#         self.assertIn("Required field 'nonexistent_field' is not defined in properties", str(context.exception))
#
#     def test_input_schema_properties_not_defined_before_required(self):
#         """Test InputSchema where properties are missing before required fields are set."""
#         invalid_input_schema = {
#             "type": "object",
#             "required": ["review_text"]  # Properties must be defined before required
#         }
#         with self.assertRaises(ValidationError) as context:
#             InputSchema(**invalid_input_schema)
#         self.assertIn("Properties must be defined before specifying required fields.", str(context.exception))
#
#     def test_input_schema_with_multiple_properties(self):
#         """Test InputSchema with multiple properties."""
#         valid_input_schema = {
#             "type": "object",
#             "properties": {
#                 "review_text": {"type": "string"},
#                 "rating": {"type": "integer"},
#                 "metadata": {"type": "object"}
#             },
#             "required": ["review_text", "rating"]
#         }
#         schema = InputSchema(**valid_input_schema)
#         self.assertEqual(schema.type, "object")
#         self.assertIn("review_text", schema.properties)
#         self.assertIn("rating", schema.properties)
#         self.assertIn("review_text", schema.required)
#         self.assertIn("rating", schema.required)
#
#     def test_input_schema_with_optional_fields(self):
#         """Test InputSchema where some fields are optional."""
#         valid_input_schema = {
#             "type": "object",
#             "properties": {
#                 "review_text": {"type": "string"},
#                 "rating": {"type": "integer"},
#                 "comment": {"type": "string"}
#             },
#             "required": ["review_text"]  # Only review_text is required
#         }
#         schema = InputSchema(**valid_input_schema)
#         self.assertEqual(schema.type, "object")
#         self.assertIn("comment", schema.properties)  # "comment" is optional
#
#     def test_input_schema_with_nested_properties(self):
#         """Test InputSchema with nested properties."""
#         valid_input_schema = {
#             "type": "object",
#             "properties": {
#                 "review_text": {"type": "string"},
#                 "author": {
#                     "type": "object",
#                     "properties": {
#                         "name": {"type": "string"},
#                         "email": {"type": "string"}
#                     },
#                     "required": ["name"]
#                 }
#             },
#             "required": ["review_text"]
#         }
#         schema = InputSchema(**valid_input_schema)
#         self.assertEqual(schema.type, "object")
#         self.assertIn("author", schema.properties)
#         self.assertIn("name", schema.properties["author"]["properties"])
#
#     def test_input_schema_empty_properties(self):
#         """Test InputSchema with empty properties and required fields."""
#         invalid_input_schema = {
#             "type": "object",
#             "properties": {},  # Empty properties
#             "required": ["review_text"]
#         }
#         with self.assertRaises(ValidationError) as context:
#             InputSchema(**invalid_input_schema)
#         self.assertIn("Properties must be defined before specifying required fields", str(context.exception))
#
#     def test_input_schema_invalid_properties_type(self):
#         """Test InputSchema with invalid type for properties fields (e.g., integer instead of string)."""
#         invalid_input_schema = {
#             "type": "object",
#             "properties": {
#                 "review_text": {"type": 12345}  # Invalid type, should be "string"
#             },
#             "required": ["review_text"]
#         }
#         with self.assertRaises(ValidationError) as context:
#             InputSchema(**invalid_input_schema)
#         self.assertIn("Each 'type' in properties must be a string", str(context.exception))
#
#
# class TestOutputSchema(unittest.TestCase):
#
#     def test_output_schema_valid(self):
#         """Test a valid OutputSchema."""
#         valid_output_schema = {
#             "type": "object",
#             "properties": {
#                 "sentiment": {"type": "string"}
#             }
#         }
#         schema = OutputSchema(**valid_output_schema)
#         self.assertEqual(schema.type, "object")
#         self.assertEqual(schema.properties["sentiment"]["type"], "string")
#
#     def test_output_schema_invalid_type(self):
#         """Test OutputSchema with an invalid type."""
#         invalid_output_schema = {
#             "type": "invalid_type",  # Invalid type, should be "object"
#             "properties": {
#                 "sentiment": {"type": "string"}
#             }
#         }
#         with self.assertRaises(ValidationError) as context:
#             OutputSchema(**invalid_output_schema)
#         self.assertIn("must be 'object'", str(context.exception))
#
#     def test_output_schema_with_nested_properties(self):
#         """Test OutputSchema with nested properties."""
#         valid_output_schema = {
#             "type": "object",
#             "properties": {
#                 "sentiment": {"type": "string"},
#                 "metadata": {
#                     "type": "object",
#                     "properties": {
#                         "confidence": {"type": "number"},
#                         "source": {"type": "string"}
#                     }
#                 }
#             }
#         }
#         schema = OutputSchema(**valid_output_schema)
#         self.assertEqual(schema.type, "object")
#         self.assertIn("metadata", schema.properties)
#         self.assertIn("confidence", schema.properties["metadata"]["properties"])
#
#     def test_output_schema_invalid_nested_property(self):
#         """Test OutputSchema with an invalid type inside nested properties."""
#         invalid_output_schema = {
#             "type": "object",
#             "properties": {
#                 "sentiment": {"type": "string"},
#                 "metadata": {
#                     "type": "object",
#                     "properties": {
#                         "confidence": {"type": "invalid_type"}  # Invalid type inside nested property
#                     }
#                 }
#             }
#         }
#         with self.assertRaises(ValidationError) as context:
#             OutputSchema(**invalid_output_schema)
#         self.assertIn("Type 'invalid_type' in properties must be one of", str(context.exception))
#
#
#
# class TestApplicationCreateRequest(unittest.TestCase):
#
#     def test_application_create_request_valid(self):
#         """Test a valid ApplicationCreateRequest."""
#         valid_application_request = {
#             "prompt_config": "You are an advanced sentiment analysis tool.",
#             "input_schema": {
#                 "type": "object",
#                 "properties": {
#                     "review_text": {"type": "string"}
#                 },
#                 "required": ["review_text"]
#             },
#             "output_schema": {
#                 "type": "object",
#                 "properties": {
#                     "sentiment": {"type": "string"}
#                 }
#             }
#         }
#         app_request = ApplicationCreateRequest(**valid_application_request)
#         self.assertEqual(app_request.prompt_config, "You are an advanced sentiment analysis tool.")
#
#     def test_application_create_request_empty_prompt_config(self):
#         """Test ApplicationCreateRequest with an empty prompt_config."""
#         invalid_application_request = {
#             "prompt_config": "",
#             "input_schema": {
#                 "type": "object",
#                 "properties": {
#                     "review_text": {"type": "string"}
#                 },
#                 "required": ["review_text"]
#             },
#             "output_schema": {
#                 "type": "object",
#                 "properties": {
#                     "sentiment": {"type": "string"}
#                 }
#             }
#         }
#         with self.assertRaises(ValidationError) as context:
#             ApplicationCreateRequest(**invalid_application_request)
#         self.assertIn("Prompt configuration cannot be empty", str(context.exception))
#
#     def test_application_create_request_whitespace_prompt_config(self):
#         """Test ApplicationCreateRequest with a whitespace-only prompt_config."""
#         invalid_application_request = {
#             "prompt_config": "   ",  # Only whitespace
#             "input_schema": {
#                 "type": "object",
#                 "properties": {
#                     "review_text": {"type": "string"}
#                 },
#                 "required": ["review_text"]
#             },
#             "output_schema": {
#                 "type": "object",
#                 "properties": {
#                     "sentiment": {"type": "string"}
#                 }
#             }
#         }
#         with self.assertRaises(ValidationError) as context:
#             ApplicationCreateRequest(**invalid_application_request)
#         self.assertIn("Prompt configuration cannot be empty", str(context.exception))
#
#     def test_application_create_request_invalid_input_schema(self):
#         """Test ApplicationCreateRequest with an invalid input_schema."""
#         invalid_application_request = {
#             "prompt_config": "You are an advanced sentiment analysis tool.",
#             "input_schema": {
#                 "type": "invalid_type",  # Invalid type for input schema
#                 "properties": {
#                     "review_text": {"type": "string"}
#                 },
#                 "required": ["review_text"]
#             },
#             "output_schema": {
#                 "type": "object",
#                 "properties": {
#                     "sentiment": {"type": "string"}
#                 }
#             }
#         }
#         with self.assertRaises(ValidationError) as context:
#             ApplicationCreateRequest(**invalid_application_request)
#         self.assertIn("must be 'object'", str(context.exception))
#
#     def test_application_create_request_invalid_output_schema(self):
#         """Test ApplicationCreateRequest with an invalid output_schema."""
#         invalid_application_request = {
#             "prompt_config": "You are an advanced sentiment analysis tool.",
#             "input_schema": {
#                 "type": "object",
#                 "properties": {
#                     "review_text": {"type": "string"}
#                 },
#                 "required": ["review_text"]
#             },
#             "output_schema": {
#                 "type": "invalid_type",  # Invalid type for output schema
#                 "properties": {
#                     "sentiment": {"type": "string"}
#                 }
#             }
#         }
#         with self.assertRaises(ValidationError) as context:
#             ApplicationCreateRequest(**invalid_application_request)
#         self.assertIn("must be 'object'", str(context.exception))
#
#     def test_application_create_request_with_complex_nested_schemas(self):
#         """Test ApplicationCreateRequest with complex nested input and output schemas."""
#         valid_application_request = {
#             "prompt_config": "You are an advanced sentiment analysis tool.",
#             "input_schema": {
#                 "type": "object",
#                 "properties": {
#                     "review_text": {"type": "string"},
#                     "author": {
#                         "type": "object",
#                         "properties": {
#                             "name": {"type": "string"},
#                             "email": {"type": "string"}
#                         },
#                         "required": ["name"]
#                     }
#                 },
#                 "required": ["review_text"]
#             },
#             "output_schema": {
#                 "type": "object",
#                 "properties": {
#                     "sentiment": {"type": "string"},
#                     "metadata": {
#                         "type": "object",
#                         "properties": {
#                             "confidence": {"type": "number"},
#                             "source": {"type": "string"}
#                         }
#                     }
#                 }
#             }
#         }
#         app_request = ApplicationCreateRequest(**valid_application_request)
#         self.assertEqual(app_request.prompt_config, "You are an advanced sentiment analysis tool.")
#         self.assertIn("author", app_request.input_schema.properties)
#         self.assertIn("metadata", app_request.output_schema.properties)
#
# if __name__ == '__main__':
#     unittest.main()
