import sys, os, operator
from typing import Annotated, TypedDict, Union, Dict, Any
import json

from dotenv import load_dotenv
from langchain_fireworks import ChatFireworks
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from .data_classes import validate_output_against_schema
from .cust_logger import logger, set_files_message_color
from datetime import datetime

set_files_message_color('MAGENTA')

# loads and checks if env var exists before continuing to model invocation
load_dotenv()
env_var_key = "FIREWORKS_API_KEY"
model_path = os.getenv(env_var_key)

# If the API key is missing, log a fatal error and exit the application, no need to run LLM application without model!
if not model_path:
    logger.fatal(f"Fatal Error: The '{env_var_key}' environment variable is missing.")
    sys.exit(1)

try:
    llm = ChatFireworks(
        model="accounts/fireworks/models/firefunction-v2",
        temperature=0.0,
        streaming=True,
        max_tokens=256
    )
    logger.info({"timestamp": datetime.now().isoformat(), "msg": "Model initialized successfully. Ready to use!", "data": f"with {env_var_key}"})
except Exception as e:
    # Log error if model initialization fails, exits. no vroom vroom :(
    logger.fatal(f"Fatal Error: Failed to initialize model: {e}")
    sys.exit(1)

class GraphsState(TypedDict):
    internal_hist: Annotated[list[str], operator.add]

graph = StateGraph(GraphsState)

def _call_model(state: GraphsState, config: RunnableConfig):
    internal_hist = state["internal_hist"]
    user_msg = internal_hist[0]
    error_hist = internal_hist[1:]
    app_data = config["configurable"]["app_details"]
    app_uuid = app_data["uuid"]
    app_prompt = app_data['prompt']
    input_schema_properties = app_data['input_schema']["properties"]
    output_schema_properties = app_data['output_schema']["properties"]
    app_logs = app_data['app_logs']

    template = """
    you are an application here is the objective below:

    {prompt}

    the message history between the application and the user so far is:
    {app_logs}

    the user's message is:
    {user_msg} that uses the input_schema of {input_schema_properties}

    the output should be following this JSON Schema:
    {output_schema_properties}

    respond in JSON format, dont add any preamble

    your previous attempts are below and caused these malformation errors:
    {errors}
    """
    prompt = PromptTemplate(
        template=template,
        input_variables=["prompt", "app_logs", "user_msg", "errors", "input_schema_properties", "output_schema_properties"],
    )

    final_prompt = prompt.format(
        prompt=app_prompt,
        app_logs=app_logs,
        user_msg=user_msg,
        errors=error_hist,
        input_schema_properties=input_schema_properties,
        output_schema_properties=output_schema_properties
    )

    log_data = {
        "internal_hist": internal_hist,
        "user_msg": user_msg,
        "error_hist": error_hist,
        "app_prompt": app_prompt,
        "input_schema_properties": input_schema_properties,
        "output_schema_properties": output_schema_properties,
        "app_logs": app_logs
    }

    logger.info({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "Calling model with formatted prompt.", "data": log_data})
    response = llm.invoke(final_prompt)

    return {"internal_hist": [response.content]}

def conditional_check(state: GraphsState, config: RunnableConfig):
    app_uuid = config["configurable"]["app_details"]["uuid"]
    last_msg = state["internal_hist"][-1]
    logger.info({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "Model response received.", "data": last_msg})
    if isinstance(last_msg, str) and last_msg.startswith('{') and last_msg.endswith('}'):
        try:
            json_object = json.loads(last_msg)
            app_data = config["configurable"]["app_details"]
            output_schema = app_data['output_schema']
            validation_errors = validate_output_against_schema(json_object, output_schema)
            if validation_errors:
                logger.error({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "Schema validation failed with errors", "data": f"{', '.join(validation_errors)}"})
                return {"internal_hist": [f"ERROR_SCHEMA - {', '.join(validation_errors)}"]}
            return state
        except json.JSONDecodeError as e:
            logger.error({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "JSON decoding failed", "data": f"{e}"})
            return {"internal_hist": [f"ERROR_JSON - converting string to JSON: {e}"]}
    else:
        logger.error({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "Invalid response format. Expected JSON.", "data": last_msg})
        return {"internal_hist": ["ERROR_JSON - Invalid response format. Respond only in JSON starting with `{` and ending with `}`"]}

def should_retry(state: GraphsState, config: RunnableConfig):
    app_uuid = config["configurable"]["app_details"]["uuid"]
    last_msg = state["internal_hist"][-1]
    if isinstance(last_msg, str) and last_msg.startswith('ERROR'):
        logger.warning({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "Error detected in last message, retrying.", "data": ""})
        return True
    logger.info({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "response is valid", "data": ""})
    return False

graph.add_node("retry_check", conditional_check)
graph.add_node("model_node", _call_model)
graph.add_edge(START, "model_node")
graph.add_edge("model_node", "retry_check")
graph.add_conditional_edges(
    "retry_check",
    should_retry,
    {
        True: "model_node",
        False: END
    }
)

graph_runnable = graph.compile()

async def ainvoke_our_graph(message: Union[str, dict], app_details: Dict[str, Any]):
    thread_config = {"configurable": {"app_details": app_details}}
    print()
    if isinstance(message, dict):
        message = json.dumps(message)
    messages = await graph_runnable.ainvoke({"internal_hist": [message]}, thread_config)
    resp = messages["internal_hist"][-1]
    logger.info({"timestamp": datetime.now().isoformat(), "uuid": app_details["uuid"], "msg": "Graph invocation complete", "data": resp})
    return resp
