# Smol Agents

A collection of small, focused agents built with the `smolagents` library.

## Available Agents

### E2B Sandbox Agent
Agent for executing code in a secure E2B sandbox environment.

**Tools:**
- `DuckDuckGoSearchTool` - Search the web for information

### Docker Sandbox Agent
Agent for executing code in isolated Docker containers.

**Tools:**
- `DuckDuckGoSearchTool` - Search the web for information

### Weather Agent
Agent for retrieving weather information.

**Tools:**
- `get_weather` - Get current weather at a given location
- `get_weather_forecast_today` - Get today's weather forecast for a location
- `get_weather_forecast_days` - Get weather forecast for multiple days at a location

### Akademiks Agent - WIP
Agent for retrieving information about DJ Akademiks' streams.

**Tools:**
- `get_latest_stream_date` - Get the date of DJ Akademiks' latest stream
- `get_latest_stream_topics` - Get the topics discussed in the latest stream

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file:
```
# Required for all agents
OPENAI_MODEL=your_openai_model
OPENAI_API_URL=your_openai_api_url
API_KEY=your_api_key

# Required for Weather Agent
GEOCODE_API_KEY=your_geocode_api_key
API_NINJAS_KEY=your_api_ninjas_key

# Required for Docker Sandbox Agent
HF_TOKEN=your_huggingface_token
```

3. Run the agents:
```
# Run weather agent
python weather.py

# Run akademiks agent
python akademiks.py

# Run E2B sandbox agent
python sandbox_execution_e2b.py

# Run Docker sandbox agent (requires Docker)
cd sandbox_execution_docker
./exec.sh
```

## Docker Sandbox Requirements
- Docker installed and running
- Python Docker SDK: `pip install docker`
