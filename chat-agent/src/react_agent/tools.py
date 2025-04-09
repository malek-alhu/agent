"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

from typing import Dict, Any
from langchain_core.tools import tool

@tool
def get_btc_statistics() -> Dict[str, Any]:
    """Fetches mocked Bitcoin (BTC) statistics like price and 24-hour change."""
    print("--- Called Mock BTC Tool ---") # Added print for debugging/visibility
    return {
        "price": "$65,432.10",
        "change_24h": "+2.1%",
        "market_cap": "$1.2T",
        "source": "MockData Inc."
    }

TOOLS = [get_btc_statistics]
