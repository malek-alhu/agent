# Documentation Plan: chat-agent

This document outlines the plan for creating comprehensive documentation for the `chat-agent` project.

## 1. Project Overview

*   **Purpose:** Describe the agent as a conversational AI built with LangChain/LangGraph to interact with the Quantics financial statistics API.
*   **Technologies:** List key technologies: Python, LangChain, LangGraph, Pydantic, httpx.

## 2. Core Architecture (LangGraph)

*   **Execution Flow:** Explain the agent's execution flow managed by LangGraph (defined in `graph.py`).
*   **Components:**
    *   **State:** The `State` object (`state.py`) holding conversation history (`messages`) and other data.
    *   **Nodes:**
        *   `call_model`: Interacts with the LLM, decides actions/responses.
        *   `tools`: Executes Quantics API tools (`ToolNode`).
        *   `process_tool_results`: Parses tool output, formats summary.
    *   **Edges:** Detail state transitions based on LLM output (tool calls vs. direct response).
*   **Diagram:** Include a Mermaid diagram illustrating the flow:
    ```mermaid
    graph TD
        A["__start__"] --> B(call_model);
        B -- "Tool Call?" --> C{route_model_output};
        C -- "Yes" --> D(tools);
        C -- "No" --> E["__end__"];
        D --> F(process_tool_results);
        F --> B;
    ```

## 3. Quantics Tools

*   **Dynamic Creation:** Explain the dynamic tool creation process (`tools.py:create_quantics_tool`) based on `stats_config.py`.
*   **Available Tools:** List current tools: Volatility, Volume, Cumulative Price.
*   **Common Tool Input (`QuanticsToolInput`):**
    *   Detail parameters (`asset`, `start_date`, `end_date`, `bar_period`, `time_filters`, `trading_hours`).
    *   **Modifying Input Validation:**
        *   Explain validation uses Pydantic (`QuanticsToolInput` in `tools.py`).
        *   Provide examples of modifying `@validator` functions or adding new ones.
*   **Common Tool Output (`QuanticsApiResponseModel`):**
    *   Describe the response structure (`success`, `charts_html`, `metadata`, `error`, `stat_output_description`).
*   **API Interaction (`_call_quantics_stat_api`):**
    *   Explain the generic API call function.
*   **Authentication (`get_quantics_auth`):**
    *   Describe the process.
    *   **Note:** Highlight current hardcoded credentials and the intended use of `.env` variables (`QUANTICS_EMAIL`, `QUANTICS_PASSWORD`).
*   **Adding New Quantics Tools:**
    *   Step 1: Identify the new statistic's API endpoint name.
    *   Step 2: Add a new dictionary entry to `AVAILABLE_STATS` in `stats_config.py` (include `name`, `description`, `output_description`).
    *   Step 3: Explain automatic registration via the dynamic tool factory in `tools.py`.

## 4. Configuration & Agent Behavior

*   **Configuration Class:** Explain `Configuration` dataclass (`configuration.py`) and parameters (`system_prompt`, `model`).
*   **Influencing Agent Behavior & Tool Usage:**
    *   **System Prompt:** Explain its role (`prompts.py`, set via `Configuration`) in defining persona and task understanding.
    *   **Tool Descriptions:** Emphasize the importance of clear `description` fields in `stats_config.py` for LLM tool selection.
    *   **Guiding JSON Generation:** Explain how LangChain's `@tool` exposes the Pydantic schema (`QuanticsToolInput`) and how clear descriptions within the model help the LLM generate correct JSON input.

## 5. State Management (`state.py`)

*   Describe the `State` dataclass extending `InputState`.
*   Explain `messages` (using `add_messages`) and `is_last_step`.
*   Mention optional fields (`tool_parameters`, `structured_tool_output`).

## 6. Utilities (`utils.py`)

*   Briefly describe helper functions: `load_chat_model`, `get_message_text`.

## 7. Setup & Usage (Inferred)

*   Mention dependency management (`pyproject.toml`).
*   Highlight the need for a `.env` file for Quantics credentials.

## 8. Testing

*   Acknowledge the presence of the `tests/` directory.