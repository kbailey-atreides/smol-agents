from smolagents import (
    CodeAgent, 
    OpenAIServerModel,
    DuckDuckGoSearchTool
)
import os

def run_agent(query):
    # Initialize the agent
    ai_model = OpenAIServerModel(
        model_id=os.getenv("OPENAI_MODEL"),
        api_base=os.getenv("OPENAI_API_URL"),
        api_key=os.getenv("API_KEY")
    )
    agent = CodeAgent(
        model=ai_model,
        tools=[DuckDuckGoSearchTool()],
        name="coder_agent",
        description="This agent takes care of your difficult algorithmic problems using code."
    )

    # Run the agent with the provided query
    response = agent.run(query)
    print(response)
    return response

if __name__ == "__main__":
    import sys
    
    # Get query from command line arguments or use a default one
    query = sys.argv[1] if len(sys.argv) > 1 else "What's the 20th Fibonacci number?"
    run_agent(query)