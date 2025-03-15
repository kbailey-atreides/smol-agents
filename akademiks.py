
from smolagents.agents import ToolCallingAgent
from smolagents import (
    tool, 
    OpenAIServerModel
)
from dotenv import load_dotenv
import os


AI_MODEL = OpenAIServerModel(
    model_id=os.getenv("OPENAI_MODEL"),
    api_base=os.getenv("OPENAI_API_URL"),
    api_key=os.getenv("API_KEY")
)

@tool
def get_latest_stream_date() -> str:
    """
    Get the date of the latest stream.
    """
    return "DJ Akademiks' last stream was on 2023-10-10"

@tool
def get_latest_stream_topics() -> str:
    """
    Get the topics of the latest stream.
    """
    return "DJ Akademiks' last stream was about the latest trends in music and the best songs of the year."

agent = ToolCallingAgent(tools=[get_latest_stream_date, get_latest_stream_topics], model=AI_MODEL)

print("ToolCallingAgent:", agent.run("what were the most recent topics discussed?"))
