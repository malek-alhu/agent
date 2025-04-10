"""Configuration for available Quantics statistics tools."""

AVAILABLE_STATS = [
    {
        "name": "Volatility",
        "description": "Fetches volatility analysis based on price fluctuations for the specified asset and period.",
        "output_description": "The response contains volatility metrics in 'metadata' and potentially charts in 'charts_html'." # Placeholder
    },
    {
        "name": "Volume",
        "description": "Fetches trading volume analysis over specified periods for the given asset.",
        "output_description": "The response contains volume metrics in 'metadata' and potentially charts in 'charts_html'." # Placeholder
    },
    {
        "name": "Cumulative Price",
        "description": "Calculates and fetches the accumulated price movement over time for the asset.",
        "output_description": "The response contains cumulative price data in 'metadata' and potentially charts in 'charts_html'." # Placeholder
    },
    # Add more stats here as needed from the PDF documentation, e.g.:
    # {
    #     "name": "Price Change",
    #     "description": "Fetches price change statistics.",
    #     "output_description": "Describes Price Change output."
    # },
    # {
    #     "name": "RSI-Cross-Above",
    #     "description": "Detects RSI crossing above a threshold.",
    #     "output_description": "Describes RSI-Cross-Above output."
    # },
    # {
    #     "name": "MA-Cross-Below",
    #     "description": "Detects Moving Average crossing below another.",
    #     "output_description": "Describes MA-Cross-Below output."
    # },
]