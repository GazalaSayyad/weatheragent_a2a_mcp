# 🌤️ Weather Agent Framework: MCP Integration Meets A2A Coordination

sample agent demonstrating A2A + ADK + MCP working together. It leverages the new Agent2Agent (A2A) Python SDK (a2a-sdk) and v1.0.0+ of Google's Agent Development Kit (ADK), google-adk.

A modular, intelligent, and scalable framework for building autonomous weather agents using:
- 🔗 **A2A**: Agent-to-Agent communication protocol
- 🛠️ **ADK**: Agent Development Kit for workflow orchestration
- 🧩 **MCP**: Model Compute Platform for tool execution

---

## 📌 Overview

The Weather Agent Framework is designed to go beyond simple chatbots. It enables agents to:
- Fetch real-time weather data from multiple APIs
- Reason using LLMs (GPT-4, Claude, Llama, etc.)
- Collaborate with other agents (e.g., traffic, logistics)
- Act on behalf of users or systems in an intelligent, autonomous way

---

## ⚙️ Architecture

### 🧩 Model Compute Platform (MCP)

MCP acts as the agent’s real-time data access layer.

#### Features:
- API abstraction via tool wrappers (e.g., OpenWeatherMap, Open-Meteo)
- Real-time and historical weather data retrieval
- Tool registry and execution orchestration

#### Components:
- **MCP Server**: Manages tool discovery and execution
- **Weather MCP Tool**: Plugin that calls real-world weather APIs

---

### 🛠️ Agent Development Kit (ADK)

ADK provides the agent brain and workflow engine.

#### Features:
- Multi-tool orchestration and chaining
- LLM-based reasoning and decision-making
- Tool interface abstraction and schema management
- Memory and context injection for rich prompts

#### Lifecycle:
1. Parse incoming weather query
2. Query MCP for tool definitions
3. Choose and execute the right tool
4. Use LLM to generate a natural language response
5. Return result to client via A2A

---

### 🔗 Agent-to-Agent (A2A) Protocol

A2A handles inter-agent communication using a lightweight, open standard.

#### Capabilities:
- Structured request routing
- Real-time or streaming response delivery
- Session management and contextual collaboration

#### Use Cases:
- Cross-domain communication (e.g., weather-to-traffic agents)
- Distributed agent networks (e.g., local weather nodes syncing regionally)
- Agent fallback and escalation patterns

🚀 Getting Started

# Prerequisites

Python 3.10+

Access to goole Gemini API (e.g., OpenAI, Anthropic)

API keys for weather services (OpenWeatherMap, Open-Meteo, etc.)

# Installation

1. git clone https://github.com/GazalaSayyad/weatheragent_a2a_mcp.git
   pip install -r requirements.txt
   cd weatheragent_a2a_mcp

2. Install uv (used to manage dependencies):
    # macOS and Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Windows (uncomment below line)

    # powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

3. Configure environment variables (via .env file):
    There are two different ways to call Gemini models:

    Calling the Gemini API directly using an API key created via Google AI Studio.
    Calling Gemini models through Vertex AI APIs on Google Cloud.

    # Environment Setup:-

    GOOGLE_API_KEY=your-openai-key
    WEATHER_API_KEY=your-weather-provider-key
    
    optional - 

    MCP_ENDPOINT=http://localhost:10000
    A2A_SERVER_URL=http://localhost:8080



#### Local Deployment
1. MCP Server
    In a terminal, start the MCP Server (it starts on port 8080):

    uv run mcp-server/server.py

2. A2A Server
    In a separate terminal, start the A2A Server (it starts on port 10000):

    uv run weather_agent

    A2A Client
    In a separate terminal, run the A2A Client to run some queries against our A2A server:

    uv run weather_agent/test_client.py


🧩 Directory Structure

    weatheragent_a2a_mcp/
    ├── weather_Agent/
    │   └── __init__.py
        └── __main__.py
        └── agent.py
        └── agent_executor.py
        └── test_client.py
    ├── mcp_server/
    │   └── server.py
        └── test_server.py
    ├── .env
    ├── README.md


📚 Further Reading

A2A Protocol - https://a2aprotocol.ai/docs/ 

ADK Developer Guide - https://google.github.io/adk-docs/

MCP Tool Registry Docs - https://modelcontextprotocol.io/docs/getting-started/intro







