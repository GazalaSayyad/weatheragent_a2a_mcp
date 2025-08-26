import logging
import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

load_dotenv()


SYSTEM_INSTRUCTION = (
    "You are a specialized assistant for weather information. "
    "Your sole purpose is to use the 'get_current_weather' tool to answer questions about current weather conditions and forecasts for a specific city. "
    "If the user asks about anything other than weather (e.g., historical weather, climate change, or non-location-based queries) "
    "or about a city you cannot find, "
    "politely state that you can only provide current weather for specified cities and cannot help with that topic. "
    "Do not attempt to answer unrelated questions or use tools for other purposes."
)


def create_agent() -> LlmAgent:
    """Constructs the ADK wather agent."""
    logger.info("--- 🔧 Loading MCP tools from MCP Server... ---")
    logger.info("--- 🤖 Creating ADK Weather Agent... ---")
    return LlmAgent(
        model="gemini-2.5-flash",
        name="weather_agent",
        description="An agent that can help with getting temperature",
        instruction=SYSTEM_INSTRUCTION,
        tools=[
            MCPToolset(
                connection_params=StreamableHTTPConnectionParams(
                    url=os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")
                )
            )
        ],
    )


root_agent = create_agent()

# import logging
# import os

# from dotenv import load_dotenv
# from google.adk.agents import LlmAgent
# from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

# logger = logging.getLogger(__name__)
# logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# load_dotenv()

# SYSTEM_INSTRUCTION = (
#     "You are a specialized assistant for currency conversions. "
#     "Your sole purpose is to use the 'get_exchange_rate' tool to answer questions about currency exchange rates. "
#     "If the user asks about anything other than currency conversion or exchange rates, "
#     "politely state that you cannot help with that topic and can only assist with currency-related queries. "
#     "Do not attempt to answer unrelated questions or use tools for other purposes."
# )


# def create_agent() -> LlmAgent:
#     """Constructs the ADK currency conversion agent."""
#     logger.info("--- 🔧 Loading MCP tools from MCP Server... ---")
#     logger.info("--- 🤖 Creating ADK Currency Agent... ---")
#     return LlmAgent(
#         model="gemini-2.5-flash",
#         name="currency_agent",
#         description="An agent that can help with currency conversions",
#         instruction=SYSTEM_INSTRUCTION,
#         tools=[
#             MCPToolset(
#                 connection_params=StreamableHTTPConnectionParams(
#                     url=os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")
#                 )
#             )
#         ],
#     )


# root_agent = create_agent()