import os
from dotenv import load_dotenv
from smolagents import  (
    CodeAgent, 
    DuckDuckGoSearchTool,
    OpenAIServerModel
)

load_dotenv()

AI_MODEL = OpenAIServerModel(
    model_id=os.getenv("OPENAI_MODEL"),
    api_base=os.getenv("OPENAI_API_URL"),
    api_key=os.getenv("API_KEY")
)

agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=AI_MODEL, executor_type="e2b")
output = agent.run("How many seconds would it take for a leopard at full speed to run through Pont des Arts?")
print("E2B executor result:", output)
