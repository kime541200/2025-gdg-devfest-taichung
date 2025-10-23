# Local Spark: AI Agent with Model Context Protocol (MCP) Demo

## Introduction
This project demonstrates an on-premise AI Agent application integrated with the Model Context Protocol (MCP). It provides a comprehensive environment for showcasing how an AI agent can interact with various services and tools through a standardized protocol.

## Features
The project is composed of four main services that work together to provide a complete AI Agent experience:

*   **FastAPI Server**: The core of the AI Agent, providing the `/v1/chat/completion` endpoint for user interaction, typically via a frontend interface like Open-WebUI.
*   **MCP Server(s)**: Multiple MCP servers that offer external tools and functionalities for the AI Agent to utilize, extending its capabilities.
*   **Open-WebUI**: A user-friendly frontend chat interface designed for easy control and interaction with the AI Agent.
*   **Inference Engine**: An OpenAI-compatible LLM inference engine that serves as the brain for the AI Agent, handling language model processing.

## Project Structure
The project is organized into several key directories:

*   `mcp/`: Contains the Model Context Protocol (MCP) server implementations.
*   `src/`: Houses the main application logic, including the FastAPI server, agent implementations, API definitions, and core utilities.
*   `config/`: Configuration files for the project.
*   `docker-compose*.yml`: Docker Compose files for orchestrating the various services.

## Setup
To get the project up and running, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd local-spark
    ```
2.  **Configure Environment Variables:**
    Copy the example environment file and modify it as needed.
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file to set up your specific configurations, such as API keys, model endpoints, and other service-specific settings.

3.  **Start the Services using Docker Compose:**
    The project uses multiple `docker-compose` files to manage different services. You will typically start them together.

    ```bash
    docker-compose -f docker-compose.yml \
                   -f docker-compose.llm.yml \
                   -f docker-compose.owui.yml \
                   -f mcp/arduino-mcp-server/docker-compose.yml \
                   up --build -d
    ```
    *   `docker-compose.yml`: Main FastAPI server.
    *   `docker-compose.llm.yml`: LLM Inference engine.
    *   `docker-compose.owui.yml`: Open-WebUI frontend.
    *   `docker-compose.think_llm.yml`: (If applicable) A separate LLM for agent's internal thinking process.
    *   `mcp/arduino-mcp-server/docker-compose.yml`: Example MCP server (e.g., for Arduino integration).

    This command will build the necessary Docker images and start all services in detached mode.

## Usage
Once all services are running:

1.  **Access Open-WebUI:**
    Open your web browser and navigate to the address where Open-WebUI is exposed (usually `http://localhost:3000` or as configured in your `docker-compose.owui.yml`).

2.  **Interact with the AI Agent:**
    Through the Open-WebUI interface, you can chat with the AI Agent. The agent will utilize the configured LLM (via the Inference Engine) and interact with the MCP servers to perform tasks and provide responses.

3.  **Monitoring Logs:**
    To view the logs of all running services, use:
    ```bash
    docker-compose -f docker-compose.yml \
                   -f docker-compose.llm.yml \
                   -f docker-compose.owui.yml \
                   -f mcp/arduino-mcp-server/docker-compose.yml \
                   logs -f
    ```

## Stopping Services
To stop and remove all running services, use:
```bash
docker-compose -f docker-compose.yml \
               -f docker-compose.llm.yml \
               -f docker-compose.owui.yml \
               -f mcp/arduino-mcp-server/docker-compose.yml \
               down
```