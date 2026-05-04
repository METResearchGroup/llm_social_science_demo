from agents.lit_review.mcp import get_tools
from agents.lit_review.state import AgentState

from langchain_openai import ChatOpenAI

LLM_MODEL = "gpt-5-nano"
TEMPERATURE = 0

async def get_papers(state: AgentState) -> AgentState:
    tools = await get_tools()
    llm = ChatOpenAI(model=LLM_MODEL, temperature=TEMPERATURE).bind_tools(tools)
    return state

def get_human_feedback(state: AgentState) -> AgentState:
    print("Human review")
    return state

def draft_summary(state: AgentState) -> AgentState:
    print("Draft summary")
    return state
