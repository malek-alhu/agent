"""This module provides tools for interacting with the Quantics API."""

import asyncio
import os
import uuid
from typing import Dict, Any, Optional, List, Type, Literal

import httpx
from dotenv import load_dotenv
from langchain_core.tools import tool
from pydantic import BaseModel, Field, ValidationError, validator

# Load environment variables from .env file
load_dotenv()

# --- Pydantic Models ---

# Define the allowed asset codes using Literal
AssetCode = Literal[
    "ES", "NQ", "DOW", "RUSS", "VIX", "EURUSD", "BP", "AUD", "JY",
    "GC", "HG", "SI", "PL", "CL", "NG", "CORN",
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"
]

class QuanticsToolInput(BaseModel):
    """Input schema for Quantics API tools."""
    asset: AssetCode = Field(
        ...,
        description="Financial instrument code. Must be one of the allowed asset codes. Required.",
        examples=["ES", "BTCUSDT"]
    )
    start_date: int = Field(
        ...,
        description="Start date in YYYYMMDD format (integer). Must be between 20120101 and 20241231. Required.",
        examples=[20230101],
        ge=20120101,
        le=20241231
    )
    end_date: int = Field(
        ...,
        description="End date in YYYYMMDD format (integer). Must be between 20120101 and 20241231, and >= start_date. Required.",
        examples=[20231231],
        ge=20120101,
        le=20241231
    )
    bar_period: int = Field(
        ...,
        description="Time frame for each bar in *minutes* (integer). Must be >= 1. Required.",
        examples=[60, 240, 1440], # Examples updated to reflect minutes
        ge=1
    )
    time_filters: Dict[str, List[bool]] = Field(
        ...,
        description="Dictionary for time filtering. Expected keys: 'months' (list[12]), 'daysOfWeek' (list[5]), 'daysOfMonth' (list[31]). Required."
    )
    trading_hours: Dict[str, int] = Field(
        ...,
        description="Dictionary for trading hours. Expected keys: 'startHour', 'startMin', 'endHour', 'endMin'. Required."
    )

    @validator('end_date')
    def end_date_must_be_after_start_date(cls, end_date, values):
        """Ensure end_date is not before start_date."""
        start_date = values.get('start_date')
        if start_date and end_date < start_date:
            raise ValueError('end_date must be greater than or equal to start_date')
        return end_date

    @validator('time_filters')
    def validate_time_filters_structure(cls, v):
        """Validate the structure of time_filters."""
        if v is None: # Should not happen if field is required, but good practice
             raise ValueError('time_filters cannot be None')

        expected_keys = {"months", "daysOfWeek", "daysOfMonth"}
        if set(v.keys()) != expected_keys:
            raise ValueError(f"time_filters must contain exactly the keys: {expected_keys}")

        if not isinstance(v["months"], list) or len(v["months"]) != 12:
            raise ValueError("time_filters['months'] must be a list of 12 booleans")
        if not all(isinstance(item, bool) for item in v["months"]):
             raise ValueError("All items in time_filters['months'] must be booleans")

        if not isinstance(v["daysOfWeek"], list) or len(v["daysOfWeek"]) != 5:
            raise ValueError("time_filters['daysOfWeek'] must be a list of 5 booleans")
        if not all(isinstance(item, bool) for item in v["daysOfWeek"]):
             raise ValueError("All items in time_filters['daysOfWeek'] must be booleans")

        if not isinstance(v["daysOfMonth"], list) or len(v["daysOfMonth"]) != 31:
            raise ValueError("time_filters['daysOfMonth'] must be a list of 31 booleans")
        if not all(isinstance(item, bool) for item in v["daysOfMonth"]):
             raise ValueError("All items in time_filters['daysOfMonth'] must be booleans")

        return v

    @validator('trading_hours')
    def validate_trading_hours_structure(cls, v):
        """Validate the structure and values of trading_hours."""
        if v is None: # Should not happen if field is required
            raise ValueError('trading_hours cannot be None')

        expected_keys = {"startHour", "startMin", "endHour", "endMin"}
        if set(v.keys()) != expected_keys:
            raise ValueError(f"trading_hours must contain exactly the keys: {expected_keys}")

        start_hour = v["startHour"]
        start_min = v["startMin"]
        end_hour = v["endHour"]
        end_min = v["endMin"]

        if not isinstance(start_hour, int) or not (0 <= start_hour <= 23):
            raise ValueError("trading_hours['startHour'] must be an integer between 0 and 23")
        if not isinstance(start_min, int) or not (0 <= start_min <= 59):
            raise ValueError("trading_hours['startMin'] must be an integer between 0 and 59")
        if not isinstance(end_hour, int) or not (0 <= end_hour <= 23):
            raise ValueError("trading_hours['endHour'] must be an integer between 0 and 23")
        if not isinstance(end_min, int) or not (0 <= end_min <= 59):
            raise ValueError("trading_hours['endMin'] must be an integer between 0 and 59")

        # Optional: Add check for end time > start time if needed, but not in current plan
        # if (end_hour * 60 + end_min) <= (start_hour * 60 + start_min):
        #     raise ValueError("Trading hours end time must be after start time")

        return v
class QuanticsApiResponseModel(BaseModel):
    """Output schema for Quantics API responses."""
    success: bool
    charts_html: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
# --- Authentication ---

# NOTE: Caching removed to address potential token expiry issues.
# This forces a login attempt before every API call.
# Consider implementing proper token refresh logic for production.
# _auth_lock = asyncio.Lock() # Lock removed as caching is disabled

# Constants
QUANTICS_LOGIN_URL = "https://quantics.srl/firebase/login"

async def get_quantics_auth() -> tuple[str, str]:
    """
    Retrieves Quantics userId and token, logging in if necessary.
    Uses an in-memory cache. Thread-safe for async calls.

    Returns:
        A tuple containing (userId, token).

    Raises:
        ValueError: If email/password environment variables are not set.
        RuntimeError: If login fails or API response is unexpected.
    """
    # Caching logic removed - proceed directly to login attempt
    print("--- Attempting Quantics Login ---")
    # --- DEBUGGING: Hardcoded credentials ---
    # REMEMBER TO REMOVE THIS AND REVERT TO os.getenv() LATER
    email = "test@test.com"
    password = "12345678"
    print(f"--- DEBUG: Using hardcoded email: {email} ---")
    # --- END DEBUGGING ---

    # Removed check for env vars as they are hardcoded for debugging
    # if not email or not password:
    #     raise ValueError("QUANTICS_EMAIL and QUANTICS_PASSWORD environment variables must be set.")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                QUANTICS_LOGIN_URL,
                json={"email": email, "password": password},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Origin": "https://quantics.app", # Added based on curl
                    "Referer": "https://quantics.app/", # Added based on curl
                }
            )
            response.raise_for_status() # Raise exception for 4xx/5xx errors

            data = response.json()
            if data.get("success") and "uid" in data and "token" in data:
                user_id = data["uid"]
                token = data["token"]
                print("--- Quantics Login Successful ---")
                # Return directly, don't cache
                return user_id, token
            else:
                error_msg = data.get("error", "Login failed, unexpected response format.")
                raise RuntimeError(f"Quantics login failed: {error_msg}")

    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Quantics login HTTP error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Quantics login request error: {e}") from e
    except Exception as e:
        # Catch any other unexpected errors during login
        raise RuntimeError(f"An unexpected error occurred during Quantics login: {e}") from e
# --- Generic API Caller ---

QUANTICS_API_BASE_URL = "https://quantics.srl/api/"

async def _call_quantics_stat_api(stat_name: str, input_data: QuanticsToolInput) -> QuanticsApiResponseModel:
    """
    Generic helper function to call a specific Quantics statistic API endpoint.

    Args:
        stat_name: The name of the statistic endpoint (e.g., "Volatility").
        input_data: Validated Pydantic model containing input parameters.

    Returns:
        A Pydantic model instance representing the API response.
    """
    try:
        user_id, token = await get_quantics_auth()
    except (ValueError, RuntimeError) as auth_err:
        # Propagate auth errors as a failure response
        return QuanticsApiResponseModel(success=False, error=f"Authentication failed: {auth_err}")

    request_id = str(uuid.uuid4()) # Generate unique ID for this request
    api_url = f"{QUANTICS_API_BASE_URL}{stat_name}?userId={user_id}"

    # Construct the nested request body from the Pydantic model
    request_body = {
        "general": {
            "asset": input_data.asset,
            "barPeriod": input_data.bar_period,
            "startDate": input_data.start_date,
            "endDate": input_data.end_date,
        },
        "stats": [stat_name],
        "id": request_id,
    }
    # Add optional filters if provided
    if input_data.time_filters:
        request_body["timeFilters"] = input_data.time_filters
    if input_data.trading_hours:
        request_body["tradingHours"] = input_data.trading_hours

    headers = {
        "Authorization": f"Firebase-Token {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    print(f"--- Calling Quantics API: {stat_name} for asset {input_data.asset} ---")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client: # Added timeout
            response = await client.post(api_url, json=request_body, headers=headers)
            response.raise_for_status() # Check for HTTP errors

            response_data = response.json()

            # Basic validation of expected structure before Pydantic parsing
            if "data" not in response_data or "metadata" not in response_data:
                 raise ValueError("API response missing expected 'data' or 'metadata' keys.")

            # Parse and validate using Pydantic model
            # We map the API's structure to our simpler response model
            api_response = QuanticsApiResponseModel(
                success=response_data.get("metadata", {}).get("success", False),
                charts_html=response_data.get("data", {}).get("charts_html"),
                metadata=response_data.get("metadata"),
                error=response_data.get("error") # Include error if API reports one
            )
            print(f"--- Quantics API Call Successful: {stat_name} ---")
            return api_response

    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        print(f"--- Quantics API HTTP Error: {stat_name} - {e.response.status_code} --- Detail: {error_detail}")
        return QuanticsApiResponseModel(success=False, error=f"API HTTP error {e.response.status_code}: {error_detail}")
    except httpx.RequestError as e:
        print(f"--- Quantics API Request Error: {stat_name} --- Error: {e}")
        return QuanticsApiResponseModel(success=False, error=f"API request error: {e}")
    except (ValueError, ValidationError, KeyError) as e: # Catch JSON parsing, validation, or key errors
        print(f"--- Quantics API Response Processing Error: {stat_name} --- Error: {e}")
        return QuanticsApiResponseModel(success=False, error=f"API response processing error: {e}")
    except Exception as e:
        # Catch any other unexpected errors during API call/processing
        print(f"--- Unexpected Error during Quantics API call: {stat_name} --- Error: {e}")
        return QuanticsApiResponseModel(success=False, error=f"An unexpected error occurred: {e}")

# --- Dynamic Tool Factory ---

# Configuration for available statistics tools
# Add more entries based on the Quantics API documentation
AVAILABLE_STATS = [
    {
        "name": "Volatility",
        "description": "Fetches volatility analysis based on price fluctuations for the specified asset and period.",
    },
    {
        "name": "Volume",
        "description": "Fetches trading volume analysis over specified periods for the given asset.",
    },
    {
        "name": "Cumulative Price",
        "description": "Calculates and fetches the accumulated price movement over time for the asset.",
    },
    # Add more stats here as needed from the PDF documentation, e.g.:
    # { "name": "Price Change", "description": "Fetches price change statistics." },
    # { "name": "RSI-Cross-Above", "description": "Detects RSI crossing above a threshold." },
    # { "name": "MA-Cross-Below", "description": "Detects Moving Average crossing below another." },
]

def create_quantics_tool(stat_config: dict) -> Any:
    """
    Factory function to dynamically create LangChain tools for Quantics statistics.

    Args:
        stat_config: A dictionary containing 'name' and 'description' for the statistic.

    Returns:
        A LangChain tool function configured for the specific statistic.
    """
    stat_name = stat_config["name"]
    stat_description = stat_config["description"]

    # Define the inner function that will become the actual tool
    # It accepts the Pydantic model directly as input
    async def dynamic_tool_func(input_data: QuanticsToolInput) -> Dict[str, Any]:
        """Dynamically generated tool function for Quantics API."""
        # The actual logic is delegated to the generic caller
        response_model = await _call_quantics_stat_api(stat_name=stat_name, input_data=input_data)
        # Return the response as a dictionary, as expected by LangChain ToolNode
        # Ensure None values are included if needed by downstream processing, or use exclude_none=True otherwise
        return response_model.model_dump()

    # Decorate the inner function with @tool.
    # LangChain automatically uses the Pydantic type hint (QuanticsToolInput)
    # to generate the schema and handle input validation.
    langchain_tool = tool(dynamic_tool_func)

    # Configure the tool's metadata
    # Use a sanitized name for the tool function if needed, but keep original name for API call
    # For LangChain, the tool name should be Python identifier compliant if used directly
    # However, LangGraph typically identifies tools by the name attribute set here.
    tool_func_name = stat_name.replace(" ", "_").replace("-", "_") # Basic sanitization for potential use as func name
    langchain_tool.name = tool_func_name # Use sanitized name for LangChain tool registry
    langchain_tool.description = stat_description
    # The args_schema is automatically derived from QuanticsToolInput by @tool

    # Store original API stat name if needed elsewhere, though not strictly necessary for tool execution here
    # setattr(langchain_tool, 'api_stat_name', stat_name)

    return langchain_tool
# --- Tool Registration ---
# (To be implemented in Task 6)

# Initialize an empty list for tools; it will be populated dynamically
TOOLS: List[Any] = []

# --- Tool Population Logic ---
print("--- Populating Quantics Tools ---")
for stat_config in AVAILABLE_STATS:
    try:
        new_tool = create_quantics_tool(stat_config)
        TOOLS.append(new_tool)
        # Optional: print statement for verification during startup
        # print(f"Successfully created and registered tool: {new_tool.name}")
    except Exception as e:
        # Log error if tool creation fails for some reason
        print(f"Error creating tool for {stat_config.get('name', 'Unknown Stat')}: {e}")

print(f"--- Total Quantics tools populated: {len(TOOLS)} ---")
# You can add other non-Quantics tools to the TOOLS list as well if needed
# e.g., TOOLS.append(some_other_tool)
