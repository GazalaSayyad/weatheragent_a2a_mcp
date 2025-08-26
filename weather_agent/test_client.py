import asyncio
import httpx
import logging
import os
from typing import Any
from uuid import uuid4

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# NOTE: Set this to the URL where your agent is running.
# Based on common setup, it might be on port 10000.
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:10000")

def print_json_response(response: Any, description: str) -> None:
    """Helper function to print the JSON representation of a response."""
    logger.info(f"--- {description} ---")
    if hasattr(response, "root"):
        print(f"{response.root.model_dump_json(exclude_none=True)}\n")
    else:
        print(f"{response.model_dump(mode='json', exclude_none=True)}\n")

async def test_weather_query(client: A2AClient) -> None:
    """Tests a valid weather-related query."""
    logger.info("--- ☀️ Testing a valid weather query... ---")
    
    payload: dict[str, Any] = {
        'message': {
            'role': 'user',
            'parts': [{'kind': 'text', 'text': 'What is the weather in London?'}],
            'messageId': uuid4().hex,
        },
    }
    request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**payload))
    response: SendMessageResponse = await client.send_message(request)
    print_json_response(response, "✅ Valid Weather Query Response")

async def test_unrelated_query(client: A2AClient) -> None:
    """Tests an unrelated query to check for the agent's refusal logic."""
    logger.info("--- 🚫 Testing an unrelated query (currency conversion)... ---")
    
    payload: dict[str, Any] = {
        'message': {
            'role': 'user',
            'parts': [{'kind': 'text', 'text': 'weather in Paris?'}],
            'messageId': uuid4().hex,
        },
    }
    request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**payload))
    response: SendMessageResponse = await client.send_message(request)
    print_json_response(response, "❌ Unrelated Query Response")

async def main() -> None:
    """Main function to run the tests."""
    logger.info(f"--- 🔄 Connecting to agent at {AGENT_URL}... ---")
    try:
        async with httpx.AsyncClient() as httpx_client:
            # Step 1: Resolve and Fetch the Agent Card
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=AGENT_URL
            )
            logger.info(f'Attempting to fetch agent card from: {AGENT_URL}')
            final_agent_card: AgentCard = await resolver.get_agent_card()
            logger.info('Successfully fetched agent card.')

            # Step 2: Initialize the A2AClient with the fetched Agent Card
            client = A2AClient(
                httpx_client=httpx_client, 
                agent_card=final_agent_card
            )
            logger.info("--- ✅ Connection successful. ---")

            await test_weather_query(client)
            await test_unrelated_query(client)

    except Exception as e:
        logger.error(f"--- ❌ An error occurred: {e} ---", exc_info=True)
        logger.error("Ensure the agent server is running and accessible at the specified URL.")

if __name__ == "__main__":
    asyncio.run(main())