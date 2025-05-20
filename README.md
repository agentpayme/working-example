# Remote MCP Server with AgentPay Integration

This is a complete working example of a remote MCP server that provides weather data and integrates with AgentPay for usage-based billing. It demonstrates how to:

1. Create a remote MCP server using Starlette
2. Use middleware for API key management
3. Integrate with AgentPay for API key validation and usage-based billing
4. Implement MCP tools with proper error handling

This working example pairs with the [Working Example Walkthrough](https://docs.agentpay.me/mcp-server-developers/examples/working-example-python) from the AgentPay documentation.

## Prerequisites

* Python 3.10 or higher
* An AgentPay account and Service Token (see [Registering Your MCP Server]([https://docs.agentpay.me](https://docs.agentpay.me/mcp-server-developers/platform/server-registration)))
* Basic understanding of MCP (from the [official tutorial](https://modelcontextprotocol.io/quickstart/server))

## Setup

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your AgentPay Service Token:
   ```bash
   cp .env.example .env
   # Edit .env and add your Service Token
   ```

## Running the Server

Start the server:
```bash
python weather_server.py
```

The server will be available at `http://localhost:8000`.

## Usage

The server provides two MCP tools:

1. `get_alerts(state: str)`: Get weather alerts for a US state
   - Cost: 2 cents per call
   - Example: `get_alerts("CA")`

2. `get_forecast(latitude: float, longitude: float)`: Get weather forecast for a location
   - Cost: 3 cents per call
   - Example: `get_forecast(37.7749, -122.4194)`

For more details on implementing usage-based billing, see our [Charging for Usage guide](https://docs.agentpay.me/mcp-server-developers/sdk/charging-for-usage) or [SDK Reference](https://docs.agentpay.me/python-sdk-reference/consume-method).

## Testing

To test your server integration:

1. **Platform Setup**
   * Ensure that you have gone through the proper setup on [AgentPay](https://agentpay.me)
   * For more information, you can refer to the following guides: [Developer Quickstart](https://docs.agentpay.me/quickstart/developers) and [Server Registration](https://docs.agentpay.me/mcp-server-developers/platform/server-registration)
   * Retrieve an API key for your MCP Server to test with at [AgentPay](https://agentpay.me)

2. **Configure Your MCP Client**
   Create or modify your `mcp.json` configuration in your MCP Client (e.g. Claude, Cursor):
   ```json
   {
     "mcpServers": {
       "weather-server": {
         "command": "npx",
         "args": [
           "-y",
           "mcp-remote",
           "http://localhost:8000/sse",
           "--header",
           "X-AGENTPAY-API-KEY:YOUR_TEST_API_KEY",
           "--allow-http"
         ],
         "env": {}
       }
     }
   }
   ```

3. **Test the Integration**
   * Verify your client can connect to the server
   * Make test requests to both tools
   * Check usage tracking in the AgentPay Hub
   * Test error handling with invalid API keys

For detailed testing instructions, see our [Testing Guide](https://docs.agentpay.me/mcp-server-developers/examples/testing).

## Additional Resources

* [Developer Quickstart](https://docs.agentpay.me/quickstart/developers)
* [Server Registration Guide](https://docs.agentpay.me/mcp-server-developers/platform/server-registration)
* [Charging for Usage](https://docs.agentpay.me/mcp-server-developers/sdk/charging-for-usage)
* [Configuring MCP Client](https://docs.agentpay.me/mcp-client-users/configuration/configuring-mcp-remote)
* [SDK Reference](https://docs.agentpay.me/python-sdk-reference/agentpayclient)
