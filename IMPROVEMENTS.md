- better handle validation errors
- rather then returning errors one at a time append them to a list and return them all together for validate_app_construct_input
- be able to handle nested json in completion for validate input, validate_output_against_schema
- dynamically create pydantic BaseModel using pydantic.create_model
- better integration testing for mock external apis
- ws for streaming tokens
- prompt conversation/logging summary, token limitation
- more extensive input validation and cleaning

PYTHONPATH=src python -m unittest discover tests/integration
PYTHONPATH=src uvicorn src.main:app --host 0.0.0.0