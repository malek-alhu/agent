"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import datetime, timezone
import json # Import the json module
from typing import Dict, List, Literal, cast, Any

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from langchain_core.tools import tool
from react_agent.tools import TOOLS # Import the dynamically populated list

# Define allowed tools explicitly
# @tool
# def get_weather(location: str):
#     """Call to get current weather"""
#     return "Weather data"


ALLOWED_TOOLS = TOOLS # Use the imported list
from react_agent.utils import load_chat_model

# Define the function that calls the model


async def call_model(
    state: State, config: RunnableConfig
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        config (RunnableConfig): Configuration for the model run.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    configuration = Configuration.from_runnable_config(config)

    # Initialize the model with tool binding. Change the model or add more tools here.
    # Strictly bind only allowed tools
    model = load_chat_model(configuration.model).bind_tools(ALLOWED_TOOLS)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = configuration.system_prompt.format(
        system_time=datetime.now(tz=timezone.utc).isoformat()
    )

    # Get the model's response
    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages], config
        ),
    )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, I could not find an answer to your question in the specified number of steps.",
                )
            ]
        }

    # Return the model's response as a list to be added to existing messages
    return {"messages": [response]}


# Define the function that processes tool results
async def process_tool_results(state: State) -> Dict[str, Any]:
    """Processes the output of the tool node, formats a summary, and updates the state."""
    last_message = state.messages[-1]
    if not isinstance(last_message, ToolMessage):
        # This should not happen in the planned flow, but is a safeguard
        print("Warning: Expected last message to be ToolMessage, but got:", type(last_message))
        return {}

    tool_output = last_message.content
    summary = "Tool execution summary:\n"

    # Attempt to parse if it's a JSON string
    parsed_output = None
    if isinstance(tool_output, str):
        try:
            parsed_output = json.loads(tool_output)
            # If parsing succeeds, treat it as a dictionary for further processing
            tool_output = parsed_output
        except json.JSONDecodeError:
            # If it's not valid JSON, just report the raw string content
            summary += f"Received non-JSON string output: {tool_output}\n"
            # Keep tool_output as the original string for the final summary part

    if isinstance(tool_output, dict):
        # Store the structured output in state (optional per plan)
        # Note: This requires the State class to have this field defined.
        # state.structured_tool_output = tool_output # Uncomment if state is updated

        # Generate summary from the dictionary structure
        # Check for success/error keys common in our API response model
        success = tool_output.get("success")
        error_msg = tool_output.get("error")
        if success is False and error_msg:
             summary += f"Tool reported failure: {error_msg}\n"
        else:
            # Fallback for other dictionary structures if needed
            summary += f"Tool Result (parsed dict): {tool_output}\n"
            # You could add more specific parsing here if successful calls return other known keys
            # e.g., charts_html = tool_output.get("charts_html")

    elif not isinstance(tool_output, str): # Handle cases where output wasn't a string or a dict
         summary += f"Received unexpected tool output format: {type(tool_output)}\nContent: {tool_output}\n"

    # Return summary as an AIMessage to be added to the history
    # Use a unique ID related to the tool call to potentially help tracing/updates
    summary_message_id = f"ai_tool_summary_{last_message.tool_call_id}"
    return {"messages": [AIMessage(content=summary.strip(), id=summary_message_id)]}


# Define a new graph

builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the two nodes we will cycle between
builder.add_node(call_model)
builder.add_node("tools", ToolNode(ALLOWED_TOOLS, handle_tool_errors=True))
builder.add_node(process_tool_results) # Add the new node

# Set the entrypoint as `call_model`
# This means that this node is the first one called
builder.add_edge("__start__", "call_model")


def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    # Strictly route based on tool calls only
    last_message = state.messages[-1]
    return "tools" if last_message.tool_calls else "__end__"


# Add a conditional edge to determine the next step after `call_model`
builder.add_conditional_edges(
    "call_model",
    # After call_model finishes running, the next node(s) are scheduled
    # based on the output from route_model_output
    route_model_output,
)

# Remove the direct edge from tools back to call_model
# builder.add_edge("tools", "call_model")

# Add edge from `tools` to our new processing node
builder.add_edge("tools", "process_tool_results")

# Add edge from our processing node back to `call_model`
builder.add_edge("process_tool_results", "call_model")

# Compile the builder into an executable graph
# You can customize this by adding interrupt points for state updates
graph = builder.compile(
    interrupt_before=[],  # Add node names here to update state before they're called
    interrupt_after=[],  # Add node names here to update state after they're called
)
graph.name = "ReAct Agent"  # This customizes the name in LangSmith
