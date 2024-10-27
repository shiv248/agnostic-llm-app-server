import os
import sys
import operator
import json
from datetime import datetime
from typing import Annotated, TypedDict, Union, Dict, Any

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import START, END, StateGraph

from data_classes import validate_output_against_schema
from cust_logger import logger, set_files_message_color

set_files_message_color('MAGENTA') # file specific JSON logging of type
                                   # {"timestamp": "", "uuid": "", "msg": "", "data": ""}

# loads and checks if env var exists before continuing to model invocation
load_dotenv()
env_var_key = "OPENAI_API_KEY"
model_path = os.getenv(env_var_key)

# If the API key is missing, log a fatal error and exit the application, no need to run LLM application without model!
if not model_path:
    logger.fatal(f"Fatal Error: The '{env_var_key}' environment variable is missing.")
    sys.exit(1)

try:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=None,
        timeout=None,
        streaming=True
    )
    logger.info({"timestamp": datetime.now().isoformat(), "msg": "Model initialized successfully. Ready to use!", "data": f"with {env_var_key}"})
except Exception as e:
    # Log error if model initialization fails, exits. no vroom vroom :(
    logger.fatal(f"Fatal Error: Failed to initialize model: {e}")
    sys.exit(1)

# this is LangGraph's internal state, currently we are using it to manage error handling and internal history through the graph
class GraphsState(TypedDict):
    internal_hist: Annotated[list[str], operator.add]

graph = StateGraph(GraphsState)

def _call_model(state: GraphsState, config: RunnableConfig):

    # extract data from respective application details to be used within the llm invocation, giving as much detail as it is necessary
    internal_hist = state["internal_hist"]
    user_msg = internal_hist[0] # entry user message, our "goal" to answer
    error_hist = internal_hist[1:] # history of validation or other issues the model has generated that it has to fix
    app_data = config["configurable"]["app_details"]

    # extract components used for application details in the prompt
    app_uuid = app_data["uuid"]
    app_prompt = app_data['prompt']
    input_schema_properties = app_data['input_schema']["properties"]
    output_schema_properties = app_data['output_schema']["properties"]
    # these are the user facing application logs, not the system logs
    app_logs = app_data['app_logs']

    # define a prompt template to be used and filled, so that model will dynamically will be handling issues and requests
    # if you remove `respond in JSON format, dont add any preamble` and invoke the model you can see the validation work effectively
    template = """
    you do NOT have access to tools or functions, do NOT make calls to tools or functions ever.

    you are an application here is the objective below:

    {prompt}

    the message history between the application and the user so far is:


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

    # current data being used within prompt to give our output
    logger.info({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "Calling model with formatted prompt.", "data": log_data})
    response = llm.invoke(final_prompt)

    # add it to our history to be used in future nodes
    return {"internal_hist": [response.content]}

def conditional_check(state: GraphsState, config: RunnableConfig):
    # this node is meant to be quality control check, checking the validity of the LLM response structure wise and also data wise
    # if its not we tell ask the model to regenerate it with the JSON or SCHEMA errors we produced
    app_uuid = config["configurable"]["app_details"]["uuid"]
    last_msg = state["internal_hist"][-1]
    logger.info({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "Model response received.", "data": last_msg})

    # this inital QC is if the response is in JSON format, as expected
    if isinstance(last_msg, str) and last_msg.startswith('{') and last_msg.endswith('}'):
        # attempt to parse the JSON and throw errors if there are internal structure errors
        try:
            json_object = json.loads(last_msg)
            app_data = config["configurable"]["app_details"]
            output_schema = app_data['output_schema'] # JSON format of OutputSchema BaseModel
            # this checks any output SCHEMA errors, the respective app has an expected output that the response needs to conform to
            # data validity check essentally
            validation_errors = validate_output_against_schema(json_object, output_schema)
            if validation_errors:
                logger.error({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "Schema validation failed with errors", "data": f"{', '.join(validation_errors)}"})
                # we add it to history to have to model fix in next pass
                return {"internal_hist": [f"ERROR_SCHEMA - {', '.join(validation_errors)}"]}
            # everything was sucessfully valid! there are no JSON(structure) or SCHEMA(data) errors
            # we dont need to add anything to the history, and can just return the state as is
            return state
        except json.JSONDecodeError as e:
            # even though the model gave a "JSON" string, it could still be malformed structure wise
            logger.error({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "JSON decoding failed", "data": f"{e}"})
            # we add it to history to have to model fix in next pass
            return {"internal_hist": [f"ERROR_JSON - converting string to JSON: {e}"]}
    else:
        # retry with and give only JSON format
        logger.error({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "Invalid response format. Expected JSON.", "data": last_msg})
        # we add it to history to have to model fix in next pass
        return {"internal_hist": ["ERROR_JSON - Invalid response format. Respond only in JSON starting with `{` and ending with `}`"]}

def should_retry(state: GraphsState, config: RunnableConfig):
    # this is a conditional "flag" that checks if the model is completed sucessfully or should it retry by checking last message for errors
    app_uuid = config["configurable"]["app_details"]["uuid"]
    last_msg = state["internal_hist"][-1]
    # im sure theres a better way of handling checking if the previous message is an `ERROR` but this works for now
    if isinstance(last_msg, str) and last_msg.startswith('ERROR'):
        logger.warning({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "Error detected in last message, retrying.", "data": ""})
        return True
    logger.info({"timestamp": datetime.now().isoformat(), "uuid": app_uuid, "msg": "response is valid", "data": ""})
    return False

# building the graph in the order it should go, model_node -> _call_model -> should_retry? -> END/`_model_node` for retry
graph.add_edge(START, "model_node")
graph.add_node("model_node", _call_model)
graph.add_edge("model_node", "retry_check")
graph.add_node("retry_check", conditional_check)
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
    # invoke our graph asynchronously, convert string to json dict, and then do the LLM majik :)
    llm_config = {"configurable": {"app_details": app_details}}
    if isinstance(message, dict):
        message = json.dumps(message)
    messages = await graph_runnable.ainvoke({"internal_hist": [message]}, llm_config)
    # we always expect the last message to be the valid and completed "response"
    resp = messages["internal_hist"][-1]
    logger.info({"timestamp": datetime.now().isoformat(), "uuid": app_details["uuid"], "msg": "Graph invocation complete", "data": resp})
    return resp
