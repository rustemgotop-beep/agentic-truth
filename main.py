from typing import TypedDict

from langgraph.graph import END, START, StateGraph


# 1. Shared state used by every node
class State(TypedDict):
    query: str
    pro_evidence: str
    con_evidence: str
    final_answer: str


# 2. Dummy node functions


def coordinator_node(state: State):
    """Receives the question and coordinates the workflow."""
    print("Coordinator: received the question.")

    # The Coordinator has no special field in our simple State,
    # so we return the query unchanged.
    return {"query": state["query"]}


def prover_node(state: State):
    """Pretends to find evidence supporting the query."""
    print("Prover: looking for supporting evidence.")

    return {
        "pro_evidence": "Found some supporting facts."
    }


def skeptic_node(state: State):
    """Pretends to find evidence opposing the query."""
    print("Skeptic: looking for opposing evidence.")

    return {
        "con_evidence": "Found some opposing facts."
    }


def verifier_node(state: State):
    """Pretends to check both sides and create a final answer."""
    print("Verifier: checking the evidence.")

    final_answer = (
        f"Mock answer for: {state['query']}\n"
        f"Supporting evidence: {state['pro_evidence']}\n"
        f"Opposing evidence: {state['con_evidence']}"
    )

    return {
        "final_answer": final_answer
    }


# 3. Conditional routing function


def verifier_router(state: State):
    """
    Decide what happens after the Verifier.

    If a final answer exists, end the graph.
    Otherwise, send the workflow back to the Coordinator.
    """
    if state["final_answer"]:
        print("Verifier: final answer is ready -> ending graph.")
        return "finish"

    print("Verifier: no final answer yet -> retrying.")
    return "retry"


# 4. Build the graph

builder = StateGraph(State)

builder.add_node("coordinator", coordinator_node)
builder.add_node("prover", prover_node)
builder.add_node("skeptic", skeptic_node)
builder.add_node("verifier", verifier_node)

# Normal edges
builder.add_edge(START, "coordinator")
builder.add_edge("coordinator", "prover")
builder.add_edge("prover", "skeptic")
builder.add_edge("skeptic", "verifier")

# Conditional edge from the Verifier
builder.add_conditional_edges(
    "verifier",
    verifier_router,
    {
        "finish": END,
        "retry": "coordinator",
    },
)

# Compile the graph
graph = builder.compile()


# 5. Run the graph with a test question

if __name__ == "__main__":
    initial_state: State = {
        "query": "Is Python a good language for beginners?",
        "pro_evidence": "",
        "con_evidence": "",
        "final_answer": "",
    }

    final_state = graph.invoke(initial_state)

    print("\n--- FINAL ANSWER ---")
    print(final_state["final_answer"])