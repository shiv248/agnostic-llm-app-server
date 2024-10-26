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
    logger.info("Model initialized successfully.")
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

    logger.info("Calling model with prompt.")
    response = llm.invoke(final_prompt)
    logger.info("Model response received.")

    return {"internal_hist": [response.content]}

def conditional_check(state: GraphsState, config: RunnableConfig):
    last_msg = state["internal_hist"][-1]
    if isinstance(last_msg, str) and last_msg.startswith('{') and last_msg.endswith('}'):
        try:
            json_object = json.loads(last_msg)
            app_data = config["configurable"]["app_details"]
            output_schema = app_data['output_schema']
            validation_errors = validate_output_against_schema(json_object, output_schema)
            if validation_errors:
                logger.error(f"Schema validation failed with errors: {', '.join(validation_errors)}")
                return {"internal_hist": [f"ERROR_SCHEMA - {', '.join(validation_errors)}"]}
            logger.info("Schema validation passed.")
            return state
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding failed: {e}")
            return {"internal_hist": [f"ERROR_JSON - converting string to JSON: {e}"]}
    else:
        logger.error("Invalid response format. Expected JSON.")
        return {"internal_hist": ["ERROR_JSON - Invalid response format. Respond only in JSON starting with `{` and ending with `}`"]}

def should_retry(state: GraphsState):
    last_msg = state["internal_hist"][-1]
    if isinstance(last_msg, str) and last_msg.startswith('ERROR'):
        logger.info("Error detected in last message, retrying.")
        return True
    logger.info("No errors detected, no retry needed.")
    return False

# Define graph structure with appropriate logging
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
    if isinstance(message, dict):
        message = json.dumps(message)
    logger.info("Starting asynchronous graph invocation.")
    messages = await graph_runnable.ainvoke({"internal_hist": [message]}, thread_config)
    logger.info("Graph invocation completed.")
    return messages["internal_hist"][-1]
