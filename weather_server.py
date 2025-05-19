"""
Weather MCP Server with AgentPay Integration

This is a complete working example of a remote MCP server that provides weather data
and integrates with AgentPay for usage-based billing.
"""

import os
import uuid
from typing import Any, Dict, Optional
from contextvars import ContextVar

import httpx
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from mcp.server.fastmcp import FastMCP
from agentpay_sdk import AgentPayClient

# Load environment variables
load_dotenv()

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"
ALERT_COST_CENTS = 2  # 2 cents per alert check
FORECAST_COST_CENTS = 3  # 3 cents per forecast

# Initialize FastMCP
mcp = FastMCP("weather-server")

# Initialize AgentPay client
agentpay_client = AgentPayClient(service_token=os.getenv("AGENTPAY_SERVICE_TOKEN"))

# Context variable for API key
api_key_context: ContextVar[str | None] = ContextVar("api_key_context", default=None)

# Helper function for NWS API requests
async def make_nws_request(url: str) -> Optional[Dict[str, Any]]:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

# API Key middleware
class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("X-AGENTPAY-API-KEY")

        if api_key:
            try:
                # Validate API key immediately after extraction
                validation_result = agentpay_client.validate_api_key(api_key=api_key)
                if not validation_result.is_valid:
                    return JSONResponse(
                        {"error": "Unauthorized", "message": f"Invalid API Key: {validation_result.invalid_reason}"},
                        status_code=401
                    )
            except Exception as e:
                return JSONResponse(
                    {"error": "Internal Server Error", "message": "API Key validation failed"},
                    status_code=500
                )

        # Set API key in context if valid
        token = api_key_context.set(api_key)
        try:
            response = await call_next(request)
        finally:
            api_key_context.reset(token)
        return response

# MCP Tools
@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    # Get API key from context
    api_key = api_key_context.get()
    if not api_key:
        return "Error: API Key missing"

    # Charge for usage
    usage_id = str(uuid.uuid4())
    result = agentpay_client.consume(
        api_key=api_key,
        amount_cents=ALERT_COST_CENTS,
        usage_event_id=usage_id
    )

    if not result.success:
        return f"Error: {result.error_message}"

    if not state or len(state) != 2:
        return "Error: Please provide a valid two-letter US state code."

    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "No active alerts for this state."

    alerts = []
    for feature in data["features"]:
        props = feature["properties"]
        alert = f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
"""
        alerts.append(alert)

    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # Get API key from context
    api_key = api_key_context.get()
    if not api_key:
        return "Error: API Key missing"

    # Charge for usage
    usage_id = str(uuid.uuid4())
    result = agentpay_client.consume(
        api_key=api_key,
        amount_cents=FORECAST_COST_CENTS,
        usage_event_id=usage_id
    )

    if not result.success:
        return f"Error: {result.error_message}"

    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data or "properties" not in points_data:
        return "Error: Unable to fetch forecast data for this location."

    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data or "properties" not in forecast_data:
        return "Error: Unable to fetch detailed forecast."

    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

# Create Starlette app
app = Starlette(
    routes=[
        Mount("/", app=mcp.sse_app())
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(ApiKeyMiddleware)
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 