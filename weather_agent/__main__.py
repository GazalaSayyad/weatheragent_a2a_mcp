import logging
import os

import click
from dotenv import load_dotenv
import uvicorn

from agent import root_agent  # Assuming root_agent is configured for weather tasks
from agent_executor import ADKAgentExecutor

from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TaskState # Added for potential use in agent_executor logic if streaming
)


logger = logging.getLogger(__name__)

load_dotenv()


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10000)
def main(host: str, port: int):
    # Verify one of Google AI Studio or Vertex AI is being used
    if os.getenv("GOOGLE_GENAI_USE_VERTEXAI") != "TRUE" and not os.getenv(
        "GOOGLE_API_KEY"
    ):
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set and "
            "GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
        )

    # --- A2A Agent Skill definition for Weather ---
    # This skill describes what your Weather Agent can do.
    skill = AgentSkill(
        id="get_current_weather", # Unique ID for the weather tool
        name="Current Weather Lookup Tool",
        description="Provides current weather conditions for a specified city.",
        tags=["weather", "forecast", "temperature"],
        examples=["What's the weather in London?", "Tell me the temperature in New York"],
    )

    # --- A2A Agent Card definition for Weather Agent ---
    # This card represents your agent's identity and capabilities to other agents.
    agent_card = AgentCard(
        name="Weather Agent 🌦️", # Updated agent name
        description="An AI agent that provides real-time weather information for cities globally.", # Updated description
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill], # Link the new weather skill
    )

    # Create the ADK runner and executor.
    # Note: 'root_agent' would need to be implemented to use the 'get_current_weather' tool
    # (e.g., by having an internal MCP client connecting to a Weather MCP Server).
    runner = Runner(
        app_name=agent_card.name,
        agent=root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    agent_executor = ADKAgentExecutor(runner, agent_card)

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )

    server = A2AFastAPIApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()
