from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ValidationError, validator

class InputSchema(BaseModel):
    type: str
    properties: Dict[str, Dict[str, Any]]
    required: List[str]

    class Config:
        extra = "forbid" # Disallows any fields not defined in the model

    # Validate that "type" is always set to "object" for InputSchema
    @validator("type")
    def check_type(cls, v):
        if v != "object":
            raise ValueError(f"The schema 'type' must be 'object'. Found: {v}")
        return v

    # Ensures each property has a defined 'type' as a string within 'properties'
    @validator("properties")
    def check_properties(cls, v):
        if not v:
            raise ValueError("Properties must be defined.")
        for key, value in v.items():
            if not isinstance(value.get("type"), str):
                raise ValueError(f"Each 'type' in properties must be a string. Found in '{key}'.")
        return v

    # Validates that all fields in 'required' are defined in 'properties'
    @validator("required", pre=True, always=True)
    def check_required_fields(cls, v, values):
        properties = values.get("properties", {})
        if not properties:
            raise ValueError("Properties must be defined before specifying required fields.")
        if not v:
            raise ValueError("Required must be defined.")
        for field in v:
            if field not in properties:
                raise ValueError(f"Required field '{field}' is not defined in properties.")
        return v


class OutputSchema(BaseModel):
    type: str
    properties: Dict[str, Dict[str, Any]]

    class Config:
        extra = "forbid"  # Disallows any fields not defined in the model

    # Ensures 'type' is always set to "object" for OutputSchema
    @validator("type")
    def check_type(cls, v):
        if v != "object":
            raise ValueError(f"The schema 'type' must be 'object'. Found: {v}")
        return v

    # Validates that properties have valid types and recursively checks nested properties if present
    @validator("properties")
    def check_properties(cls, v):
        if not v:
            raise ValueError("Properties must not be empty.")

        valid_types = {"string", "number", "boolean", "array", "object"}

         # Checks each 'type' in properties to confirm it's valid
        for key, value in v.items():
            if "type" in value:
                if value["type"] not in valid_types:
                    raise ValueError(
                        f"Type '{value['type']}' in properties must be one of {valid_types}. Found: {value['type']} (in '{key}')"
                    )

            # If nested 'properties' are present, validate recursively
            if "properties" in value:
                nested_properties = value["properties"]
                for nested_key, nested_value in nested_properties.items():
                    # Recursive check for nested properties types
                    cls.check_properties_types(nested_value)
        return v

    # Validates 'type' for nested properties recursively
    @classmethod
    def check_properties_types(cls, v):
        valid_types = {"string", "number", "boolean", "array", "object"}
        if "type" in v and v["type"] not in valid_types:
            raise ValueError(
                f"Type '{v['type']}' in properties must be one of {valid_types}. Found: {v['type']}"
            )
        return v

class ApplicationCreateRequest(BaseModel):
    prompt_config: str
    input_schema: InputSchema
    output_schema: OutputSchema

    # Strips whitespace from 'prompt_config' and ensures it's not empty
    @validator('prompt_config')
    def strip_whitespace(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Prompt configuration cannot be empty or just whitespace.")
        return v

def validate_input_against_schema(input_data: Dict[str, Any], schema_data: Dict[str, Any]) -> Optional[List[str]]:
    """Validates input_data against schema_data in InputSchema format, input for completion from user.
       Returns a list of error messages, or None if validation passes.

       This function performs validations such as:
       - If required fields presence
       - Check correct field types
       - Disallows unexpected fields
    """

    errors = []

    # Step 1: Ensure schema_data itself is valid InputSchema
    try:
        # ** allows keyword arguments to match the schema's structure
        schema = InputSchema(**schema_data)
    except ValidationError as e:
        # Return schema validation errors if schema instantiation fails
        return [f"Schema validation error: {error['msg']}" for error in e.errors()]

    # Step 2: Validate required fields are present in input_data
    for required_field in schema.required:
        if required_field not in input_data:
            errors.append(f"Missing required field: '{required_field}'")

    # Step 3: Validates input_data field types based on schema properties
    for field_name, field_info in schema.properties.items():
        if field_name in input_data:
            expected_type = field_info["type"]
            field_value = input_data[field_name]

            # Perform type validation based on the expected acceptable schema type
            if not validate_field_type(field_value, expected_type):
                errors.append(f"Field '{field_name}' should be of type '{expected_type}'.")

    # Step 4: Check for unexpected fields in input_data
    for field_name in input_data.keys():
        if field_name not in schema.properties:
            errors.append(f"Unexpected field '{field_name}' in input data.")

    return errors if errors else None


def validate_output_against_schema(output_data: Dict[str, Any], schema_data: Dict[str, Any]) -> Optional[List[str]]:
    """Validates LLM generated output_data against OutputSchema, to send out to user.
       Returns a list of error messages, or None if validation passes.

       This function is necessary for similar reasons to validate_input, including:
       1. Dynamic schema handling with OutputSchema as JSON Schema.
       2. Iterative validation due to flexible schema properties.
    """

    errors = []

    # Step 1: Ensures schema_data itself is valid OutputSchema
    try:
        # This only confirms schema_data adheres to OutputSchema requirements (e.g., correct structure, field types).
        # ** allows keyword arguments to match the schema's structure
        schema = OutputSchema(**schema_data)
    except ValidationError as e:
        # If schema_data is invalid as a schema, return those errors immediately.
        return [f"Schema validation error: {error['msg']}" for error in e.errors()]

    # Step 2: Checks each field in schema properties exists in output_data with the correct type
    # Since OutputSchema doesn't specify required fields directly, we'll assume any field in "properties" can appear
    # in output_data, but we'll enforce the types.
    for field_name, field_info in schema.properties.items():
        if field_name in output_data:
            expected_type = field_info["type"]
            field_value = output_data[field_name]

            # Type validation for each output field
            if not validate_field_type(field_value, expected_type):
                errors.append(f"Field '{field_name}' should be of type '{expected_type}'.")

    # Step 3: Check for unexpected fields in output_data
    # Since schema_data defines allowed fields in "properties", any extra fields in output_data are flagged.
    for field_name in output_data.keys():
        if field_name not in schema.properties:
            errors.append(f"Unexpected field '{field_name}' in output data.")

    return errors if errors else None # return any list of errors


def validate_field_type(value: Any, expected_type: str) -> bool:
    """Helper function to check if a value matches the expected schema type"""
    type_map = {
        "string": str,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    # Check if the value type matches the expected type
    if expected_type in type_map:
        return isinstance(value, type_map[expected_type])
    return False

def validate_app_construct_input(request_data: Dict[str, Any]) -> Tuple[Optional[list], Optional[ApplicationCreateRequest]]:
    """Validates an ApplicationCreateRequest using request_data, for creation of application.
       Returns a tuple of (errors, validated_schema) where errors is a list of validation errors or None if successful.
    """

    try:
        validated_schema = ApplicationCreateRequest(
            prompt_config=request_data["prompt_config"],
            # ** allows keyword arguments to match the schema's structure
            input_schema=InputSchema(**request_data["input_schema"]),
            output_schema=OutputSchema(**request_data["output_schema"])
        )
    except KeyError as e:
        # Handle missing fields errors such as required ones
        return {"msg": f"Missing required field: {str(e)}"}, None
    except ValidationError as e:
        errors = []
        # Collects detailed error messages for each failed validation
        for error in e.errors():
            errors.append({"msg": error.get("msg")})
        return errors, None

    return None, validated_schema # Returns None if validation passed, along with the validated ApplicationCreateRequest instance
