from agents.lit_review.mcp import get_tools
from agents.lit_review.state import AgentState

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

LLM_MODEL = "gpt-5-nano"
TEMPERATURE = 0


def collect_query(state: AgentState) -> dict:
    """Ensure `query` is set: use CLI-provided value or prompt interactively."""
    q = (state.get("query") or "").strip()
    if not q:
        q = input("Enter your research query: ").strip()
    if not q:
        raise ValueError("A non-empty research query is required.")
    return {"query": q}


async def get_papers(state: AgentState) -> dict:
    tools = await get_tools()
    llm = ChatOpenAI(model=LLM_MODEL, temperature=TEMPERATURE).bind_tools(tools)
    user_msg = HumanMessage(
        content=(
            "Find academic papers relevant to this research query. "
            f"Query: {state['query']}"
        )
    )
    response = await llm.ainvoke([user_msg])
    return {"messages": [user_msg, response]}

def get_human_feedback(state: AgentState) -> AgentState:
    print("Human review")
    return state

def draft_summary(state: AgentState) -> AgentState:
    print("Draft summary")
    return state
