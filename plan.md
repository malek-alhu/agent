# Plan for Constraining the QUANTICS Chatbot

This document outlines the plan for constraining the QUANTICS chatbot to use only its tools and respond to questions answerable by those tools or its LangGraph knowledge.

## 1. Analyze Existing Code

*   **`react_agent/configuration.py`:** This file defines the `Configuration` class, which holds configurable parameters for the agent. The `system_prompt` attribute is particularly important, as it sets the context and behavior for the agent. The `model` attribute specifies the language model to use.
*   **`react_agent/state.py`:** This file defines the `State` class, which represents the complete state of the agent. The `State` class inherits from `InputState`, which includes a `messages` attribute that tracks the conversation history. The `State` class also includes an `is_last_step` attribute, which indicates whether the current step is the last one before the graph raises an error.
*   **`react_agent/graph.py`:** This file defines the LangGraph graph structure, including the nodes, edges, and the routing logic.
*   **`react_agent/tools.py`:** This file defines the available tools that the agent can use.

## 2. Consult LangGraph Documentation

*   **LangGraph Glossary:** This provides an overview of the key concepts associated with LangGraph graph primitives.
*   **Agent architectures:** This explains the different types of agent architectures and how they can be used to control the flow of an application.
*   **Human-in-the-Loop:** This explains different ways of integrating human feedback into a LangGraph application.

## 3. Implement Prompt Engineering

*   Modify the system prompt in `react_agent/configuration.py` to explicitly instruct the LLM to use the available tools whenever possible. The prompt should be generic enough to accommodate new tools and data sources in the future.
*   Add examples to the system prompt to demonstrate how the LLM should use the available tools.

```python
# react_agent/configuration.py

from dataclasses import dataclass, field
from typing import Annotated, Optional

from langchain_core.runnables import RunnableConfig, ensure_config

from react_agent import prompts

@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent."""

    system_prompt: str = field(
        default="""You are a helpful assistant for QUANTICS, a startup providing statistics and data analysis.
        You have access to various tools that you should use whenever possible to answer user questions.
        If the user asks a question that you cannot answer with the available tools, respond with "I cannot answer this question with the available tools."

        Here are some examples of how you should use the available tools:

        User: What is the current price of Bitcoin?
        Assistant: I can use the get_btc_statistics tool to answer that question.

        {
            "tool_calls": [
                {
                    "id": "tool_call_id",
                    "type": "function",
                    "function": {
                        "name": "get_btc_statistics",
                        "arguments": "{}"
                    }
                }
            ]
        }
        """,
        metadata={
            "description": "The system prompt to use for the agent's interactions. "
            "This prompt sets the context and behavior for the agent."
        },
    )

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-4o",
        metadata={
            "description": "The name of the language model to use for the agent's main interactions. "
            "Should be in the form: provider/model-name."
        },
    )

    max_search_results: int = field(
        default=10,
        metadata={
            "description": "The maximum number of search results to return for each search query."
        },
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})
```

*   I will also update the `prompts.py` file to reflect this change.

## 4. Implement Question Filtering

*   Modify the `route_model_output` function in `react_agent/graph.py` to check if the user's question can be answered with the available tools.
*   If the question cannot be answered with the available tools, return `__end__` to end the conversation.
*   Add a message to the user explaining that the agent cannot answer the question with the available tools.

```python
# react_agent/graph.py

from typing import Literal
from langchain_core.messages import AIMessage
from langgraph.types import Command

def route_model_output(state: State) -> Literal["__end__", "tools"]:
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    if not last_message.tool_calls:
        # Check if the user's question can be answered with the available tools
        # This is a placeholder for a more sophisticated question filtering mechanism
        # that would analyze the user's question and determine if it can be answered
        # with the available tools.
        if True: # Replace with actual question filtering logic
            return Command(update={"messages": [AIMessage(content="I cannot answer this question with the available tools.")]}, goto="__end__")
        else:
            return "__end__"
    return "tools"
```

*   **Important:** The question filtering logic in the `route_model_output` function is currently a placeholder. In a real-world scenario, this would need to be replaced with a more sophisticated mechanism that can analyze the user's question and determine if it can be answered with the available tools. This could involve using techniques such as:
    *   **Keyword matching:** Check if the user's question contains keywords related to the available tools.
    *   **Semantic similarity:** Use a language model to calculate the semantic similarity between the user's question and the descriptions of the available tools.
    *   **Question answering:** Use a question answering model to determine if the user's question can be answered using the information available in the tool descriptions.

## 5. Test and Evaluate

*   Test the agent with a variety of questions to ensure that it only answers questions that can be answered with the available tools and that it uses the tools whenever possible.
*   Evaluate the agent's performance and make adjustments to the prompt or the question filtering mechanism as needed.

## 6. Consult Documentation

*   I have consulted the LangGraph documentation to find the best way to implement the question filtering mechanism and customize the agent's response when it cannot answer a question.