import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles

from data_classes import validate_input_against_schema, validate_app_construct_input
from graph import ainvoke_our_graph
from cust_logger import logger, set_files_message_color

set_files_message_color('PURPLE')

app = FastAPI(title="LLM Application Server")

# In-memory storage for applications
applications: Dict[str, Dict] = {}

# Display frontend
static_dir = os.path.join(os.path.dirname(__file__), 'static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=FileResponse)
async def serve_index():
    logger.info({"timestamp": datetime.now().isoformat(), "msg": "New Anonymous User!"})
    return "src/static/index.html"

@app.post("/applications")
def create_application(request: Dict[str, Any]):
    # Validate application configuration input against baseline expected schema structure, respond back with validation issues if any
    errors, validated_schema = validate_app_construct_input(request)

    if errors:
        logger.error({"timestamp": datetime.now().isoformat(), "msg": "New LLM Application attempt", "data": f"errors: {errors}"})
        raise HTTPException(status_code=422, detail=errors)

    #Unique User ID (UUID) generated from backend to be application distinguishable
    application_id = str(uuid.uuid4())

    # using JSON format for easy dynamic data manipulation (parsing, unparsing, moving) across the 1 system and multiple applications
    applications[application_id] = {
        "uuid": application_id,
        "prompt": validated_schema.prompt_config,
        "input_schema": validated_schema.input_schema.model_dump(), # Flatten input/output Pydantic Basemodel schema
        "output_schema": validated_schema.output_schema.model_dump(), # into json dict to be portable
        "app_logs": [{"sender": "user", "msg": "Application Created", "timestamp": datetime.now().isoformat()}]
    }

    logger.info({"timestamp": datetime.now().isoformat(), "uuid": application_id, "msg": "New LLM Application", "data": applications[application_id]})

    return {
        "application_id": application_id
    }

@app.delete("/applications/{application_id}", response_class=Response)
def delete_application(application_id: str):
    # simple delete endpoint, with error handling if app doesn't exist
    if application_id in applications:
        del applications[application_id]
        logger.info({"timestamp": datetime.now().isoformat(), "uuid": application_id, "msg": "Application deleted", "data": "delete"})
        return Response(status_code=204) # 204 No Content but deleted object, response
    logger.info({"timestamp": datetime.now().isoformat(), "uuid": application_id, "msg": "Application already deleted", "data": "delete"})
    raise HTTPException(status_code=404, detail="Application not found")

@app.post("/applications/{application_id}/completions")
async def generate_response(application_id: str, request: Dict[str, Any]):
    # completion endpoint that handles input request validation against its respective application

    if application_id not in applications:
        logger.info({"timestamp": datetime.now().isoformat(), "uuid": application_id, "msg": "Application not found", "data": "completions"})
        raise HTTPException(status_code=404, detail="Application not found")

    # Retrieve the input schema for the respective application
    app_data = applications[application_id]
    app_data["app_logs"].append({"sender":"user", "msg":request, "timestamp":datetime.now().isoformat()})

    input_schema = app_data["input_schema"]

    # handle validation and respond back with any errors that could occur such as expected keys or extraneous keys
    errors = validate_input_against_schema(request, input_schema)

    if errors:
        logger.error({"timestamp": datetime.now().isoformat(), "uuid": application_id, "msg": "Validation Input Errors", "data": errors})
        raise HTTPException(status_code=422, detail=errors)

    # Invoke LLM to generate response (async call to avoid blocking since its the highest latency endpoint)
    resp = await ainvoke_our_graph(request, app_data)
    try:
        # we assume that the output validation from the graph/chain is agressive enough but in case its not we can still account for it
        decoded_resp = json.loads(resp)
        logger.info({"timestamp": datetime.now().isoformat(), "uuid": application_id, "msg": "Application AI Responded", "data": decoded_resp})
        app_data["app_logs"].append({"sender":"ai", "msg": decoded_resp, "timestamp":datetime.now().isoformat()})
        return decoded_resp
    except json.JSONDecodeError:
        # account for leaky json output from LLM model, always give completion
        app_data["app_logs"].append({"sender":"ai", "msg": {"message": resp}, "timestamp":datetime.now().isoformat()})
        logger.warning({"timestamp": datetime.now().isoformat(), "uuid": application_id, "msg": "Leaky JSON Output Validation", "data": resp})
        return {"message": resp}

@app.get("/applications/{application_id}/completions/logs")
def get_request_logs(application_id: str):
    # simple logs response, these are its respective application logs not system logs
    # so it only maintains interactions within the app and user, not errors from backend side
    if application_id not in applications:
        logger.info({"timestamp": datetime.now().isoformat(), "uuid": application_id, "msg": "Application not found", "data": "logs"})
        raise HTTPException(status_code=404, detail="Application not found")

    logs = applications[application_id]["app_logs"]
    return logs
