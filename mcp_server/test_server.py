import asyncio
import os
from fastmcp import Client
from typing import Dict, Any, Optional

async def test_weather_server_only():
    """
    Tests the MCP server by calling the 'get_current_weather' tool.
    This client is tailored for the server.py that only hosts the weather tool.
    """
    # Ensure your MCP server (server.py) is running at http://localhost:8080/mcp
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")
    print(f"--- 🌐 Connecting to MCP server at: {mcp_server_url} ---")

    try:
        async with Client(mcp_server_url) as client:
            # List available tools to verify 'get_current_weather' is present
            print("--- 🔍 Listing available tools ---")
            tools = await client.list_tools()
            found_weather_tool = False
            for tool in tools:
                print(f"--- 🛠️ Tool found: {tool.name} ---")
                if tool.name == "get_current_weather": # Ensure this exactly matches the server's registered tool name
                    found_weather_tool = True
            
            if not found_weather_tool:
                print("--- ❌ 'get_current_weather' tool not found on the MCP server. Ensure server.py is running and 'get_current_weather' tool is registered with the exact name. ---")
                return

            # Call get_current_weather tool for a specific city
            city_to_check = "Mumbai" # You can change this city
            units_to_use = "metric" # Or "imperial"
            print(f"\n--- 🪛 Calling get_current_weather tool for {city_to_check} ({units_to_use} units) ---")
            
            # FIXED LINE: The result of client.call_tool is a single ContentPart object.
            # We no longer attempt to iterate over it directly.
            tool_response_content_part = await client.call_tool(
                "get_current_weather", {"city": city_to_check, "units": units_to_use}
            )

            # We directly check if this single returned object has structuredContent.
            structured_content: Optional[Dict[str, Any]] = None
            if hasattr(tool_response_content_part, 'structuredContent') and tool_response_content_part.structuredContent:
                structured_content = tool_response_content_part.structuredContent

            if structured_content:
                city = structured_content.get("city", "N/A")
                temp = structured_content.get("current_temperature", "N/A")
                conditions = structured_content.get("conditions", "N/A")
                humidity = structured_content.get("humidity", "N/A")
                wind = structured_content.get("wind_speed", "N/A")
                hourly_forecast = structured_content.get("hourly_forecast_next_3_hours", [])

                print(f"\n--- ✅ Success: Weather for {city} ---")
                print(f"   Current Temperature: {temp}")
                print(f"   Conditions: {conditions}")
                print(f"   Humidity: {humidity}")
                print(f"   Wind Speed: {wind}")
                if hourly_forecast:
                    print("   Hourly Forecast (next 3 hours):")
                    for hour_data in hourly_forecast:
                        print(f"     - {hour_data.get('time')}: {hour_data.get('temperature')}")
                else:
                    print("   No hourly forecast available.")
            else:
                # If no structured content, there might be plain text or an error message
                # Access text directly from the single ContentPart object if it exists
                plain_text_output = tool_response_content_part.text if hasattr(tool_response_content_part, 'text') else str(tool_response_content_part)
                print(f"--- ⚠️ Warning: No structured content found. Raw output: {plain_text_output} ---")

    except Exception as e:
        print(f"--- ❌ Error connecting to or calling MCP server: {e} ---")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv() # Load .env file for MCP_SERVER_URL if used

    asyncio.run(test_weather_server_only())




# import asyncio

# from fastmcp import Client


# async def test_server():
#     # Test the MCP server using streamable-http transport.
#     # Use "/sse" endpoint if using sse transport.
#     async with Client("http://localhost:8080/mcp") as client:
#         # List available tools
#         tools = await client.list_tools()
#         for tool in tools:
#             print(f"--- 🛠️  Tool found: {tool.name} ---")
#         # Call get_exchange_rate tool
#         print("--- 🪛  Calling get_exchange_rate tool for USD to EUR ---")
#         result = await client.call_tool(
#             "get_exchange_rate", {"currency_from": "USD", "currency_to": "EUR"}
#         )
#         print(f"--- ✅  Success: {result[0].text} ---")


# if __name__ == "__main__":
#     asyncio.run(test_server())