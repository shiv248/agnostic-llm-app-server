from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import uuid
from datetime import datetime
import json
from typing import Dict, List, Any
from .data_classes import ApplicationCreateRequest, validate_input_against_schema, validate_app_construct_input
from .graph import ainvoke_our_graph

app = FastAPI(title="LLM Application Server")

# In-memory storage for applications
applications: Dict[str, Dict] = {}

app.mount("/static", StaticFiles(directory="src/static"), name="static")

@app.get("/", response_class=FileResponse)
async def serve_index():
    return "src/static/index.html"

@app.post("/applications")
def create_application(request: Dict[str, Any]):
    errors, validated_schema = validate_app_construct_input(request)

    if errors:
        raise HTTPException(status_code=422, detail=errors)

    application_id = str(uuid.uuid4())

    applications[application_id] = {
        "uuid": application_id,
        "prompt": validated_schema.prompt_config,
        "input_schema": validated_schema.input_schema.model_dump(),
        "output_schema": validated_schema.output_schema.model_dump(),
        "app_logs": [{"msg":"Application Created", "timestamp":datetime.now().isoformat()}]
    }

    return {
        "application_id": application_id
    }

@app.delete("/applications/{application_id}", response_class=Response)
def delete_application(application_id: str):
    if application_id in applications:
        del applications[application_id]
        return Response(status_code=204)
    raise HTTPException(status_code=404, detail="Application not found")

@app.post("/applications/{application_id}/completions")
async def generate_response(application_id: str, request: Dict[str, Any]):
    if application_id not in applications:
        raise HTTPException(status_code=404, detail="Application not found")

    # Retrieve the input schema for the application
    app_data = applications[application_id]
    app_data["app_logs"].append({"msg":request, "timestamp":datetime.now().isoformat()})

    input_schema = app_data["input_schema"]
    output_schema = app_data["output_schema"]

    errors = validate_input_against_schema(request, input_schema)

    if errors:
        raise HTTPException(status_code=422, detail=errors)

    resp = await ainvoke_our_graph(request, app_data)
    try:
        decoded_resp = json.loads(resp)
        app_data["app_logs"].append({"msg":decoded_resp, "timestamp":datetime.now().isoformat()})
        return decoded_resp
    except json.JSONDecodeError:
        app_data["app_logs"].append({"msg": {"message": resp}, "timestamp":datetime.now().isoformat()})
        return {"message": resp}

@app.get("/applications/{application_id}/completions/logs")
def get_request_logs(application_id: str):
    if application_id not in applications:
        raise HTTPException(status_code=404, detail="Application not found")

    logs = applications[application_id]["app_logs"]
    return logs
