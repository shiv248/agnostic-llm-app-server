from typing import Dict, List, Optional, Any, Union, Tuple
from pydantic import BaseModel, Field, validator, ValidationError, Extra

class InputSchema(BaseModel):
    type: str
    properties: Dict[str, Dict[str, Any]]
    required: List[str]

    class Config:
        extra = "forbid"

    # Validate that the type is always "object"
    @validator("type")
    def check_type(cls, v):
        if v != "object":
            raise ValueError(f"The schema 'type' must be 'object'. Found: {v}")
        return v

    # Ensure that each property in 'properties' has a valid 'type'
    @validator("properties")
    def check_properties(cls, v):
        if not v:
            raise ValueError("Properties must be defined.")
        for key, value in v.items():
            if not isinstance(value.get("type"), str):
                raise ValueError(f"Each 'type' in properties must be a string. Found in '{key}'.")
        return v

    # Ensure that required fields correspond to 'properties'
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
        # denies extra fields
        extra = "forbid"

    @validator("type")
    def check_type(cls, v):
        if v != "object":
            raise ValueError(f"The schema 'type' must be 'object'. Found: {v}")
        return v

    @validator("properties")
    def check_properties(cls, v):
        if not v:
            raise ValueError("Properties must not be empty.")

        valid_types = {"string", "number", "boolean", "array", "object"}

        # Validate the "type" field inside properties
        for key, value in v.items():
            if "type" in value:
                if value["type"] not in valid_types:
                    raise ValueError(
                        f"Type '{value['type']}' in properties must be one of {valid_types}. Found: {value['type']} (in '{key}')"
                    )

            # Recursively validate nested properties if they exist
            if "properties" in value:
                nested_properties = value["properties"]
                for nested_key, nested_value in nested_properties.items():
                    # Recursive check for nested properties types
                    cls.check_properties_types(nested_value)
        return v

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

    @validator('prompt_config')
    def strip_whitespace(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Prompt configuration cannot be empty or just whitespace.")
        return v

def validate_input_against_schema(input_data: Dict[str, Any], schema_data: Dict[str, Any]) -> Optional[List[str]]:
    """Validate the incoming input_data against the stored InputSchema schema_data.
        Returns a list of error messages, or None if validation passes.

        This function has to do additional validation steps beyond the ValidationError check
        because:

        1. Instantiating InputSchema with schema_data only verifies that schema_data itself is valid as a schema.
           This means it checks if the structure and types within schema_data adhere to the InputSchema model
           requirements, but it does NOT validate input_data against schema_data.

        2. InputSchema essentially acts as a JSON Schema, containing rules (such as required fields, field types,
           and nested properties) for input_data to follow. Pydantic doesn’t directly enforce these rules on
           input_data without specific field definitions, so validate_input_against_schema must interpret
           and enforce these schema rules on input_data.

        3. The properties in schema_data are dynamic and can vary depending on the use case. The flexible nature
           of schema_data["properties"] requires this function to iterate over each defined property in
           schema_data to dynamically validate that input_data fields meet the schema requirements.

        4. Checks for missing required fields, unexpected fields, and nested validations are not automatically
           handled by Pydantic for input_data. This function performs these additional checks to ensure input_data
           is fully validated according to the flexible schema specified in schema_data.
    """

    errors = []

    # Step 1: Validate the schema_data itself
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

    # Step 3: Validate the types of fields in input_data based on schema's properties
    for field_name, field_info in schema.properties.items():
        if field_name in input_data:
            expected_type = field_info["type"]
            field_value = input_data[field_name]

            # Perform type validation based on the expected schema type
            if not validate_field_type(field_value, expected_type):
                errors.append(f"Field '{field_name}' should be of type '{expected_type}'.")

    # Step 4: Check for unexpected fields in input_data
    for field_name in input_data.keys():
        if field_name not in schema.properties:
            errors.append(f"Unexpected field '{field_name}' in input data.")

    return errors if errors else None


def validate_output_against_schema(output_data: Dict[str, Any], schema_data: Dict[str, Any]) -> Optional[List[str]]:
    """Validate the outgoing output_data against the stored OutputSchema schema_data.
    Returns a list of error messages, or None if validation passes.

    This function performs additional validation steps beyond the ValidationError check
    because:

    1. Instantiating OutputSchema with schema_data only verifies that schema_data itself is valid as a schema.
       This means it checks if the structure and types within schema_data adhere to the OutputSchema model
       requirements, but it does NOT validate output_data against schema_data.

    2. OutputSchema acts as a JSON Schema, containing rules (such as required fields, field types, and nested
       properties) for output_data to follow. Pydantic doesn’t directly enforce these rules on output_data
       without specific field definitions, so validate_output_against_schema must interpret and enforce these
       schema rules on output_data.

    3. The properties in schema_data are dynamic and vary depending on the use case. The flexible nature of
       schema_data["properties"] requires this function to iterate over each defined property in schema_data
       to dynamically validate that output_data fields meet the schema requirements.

    4. Checks for unexpected fields, nested validations, and type validations are not automatically handled
       by Pydantic for output_data. This function performs these additional checks to ensure output_data is
       fully validated according to the flexible schema specified in schema_data.
    """

    errors = []

    # Step 1: Validate the schema_data itself
    try:
        # This only confirms schema_data adheres to OutputSchema requirements (e.g., correct structure, field types).
        # ** allows keyword arguments to match the schema's structure
        schema = OutputSchema(**schema_data)
    except ValidationError as e:
        # If schema_data is invalid as a schema, return those errors immediately.
        return [f"Schema validation error: {error['msg']}" for error in e.errors()]

    # Step 2: Validate required fields in schema_data (if any are specified)
    # Since OutputSchema doesn't specify required fields directly, we'll assume any field in "properties" can appear
    # in output_data, but we'll enforce the types.
    for field_name, field_info in schema.properties.items():
        if field_name in output_data:
            expected_type = field_info["type"]
            field_value = output_data[field_name]

            # Perform type validation based on the expected schema type
            if not validate_field_type(field_value, expected_type):
                errors.append(f"Field '{field_name}' should be of type '{expected_type}'.")

    # Step 3: Check for unexpected fields in output_data
    # Since schema_data defines allowed fields in "properties", any extra fields in output_data are flagged.
    for field_name in output_data.keys():
        if field_name not in schema.properties:
            errors.append(f"Unexpected field '{field_name}' in output data.")

    return errors if errors else None


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
    """Validate the ApplicationCreateRequest by attempting to instantiate it with request_data.
    Returns a tuple of (errors, validated_schema) where errors is a list of error messages, or None if validation passes.
    validated_schema is the ApplicationCreateRequest instance if validation is successful, or None if there are errors."""

    try:
        validated_schema = ApplicationCreateRequest(
            prompt_config=request_data["prompt_config"],
            # ** allows keyword arguments to match the schema's structure
            input_schema=InputSchema(**request_data["input_schema"]),
            output_schema=OutputSchema(**request_data["output_schema"])
        )
    except KeyError as e:
        # Handle missing required fields
        return {"msg": f"Missing required field: {str(e)}"}, None
    except ValidationError as e:
        errors = []
        # Extract error information in a JSON-serializable format
        for error in e.errors():
            errors.append({
                "msg": error.get("msg"),
            })
        return errors, None

    return None, validated_schema
