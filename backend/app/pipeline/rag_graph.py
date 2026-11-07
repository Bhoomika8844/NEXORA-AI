
from langgraph.graph import StateGraph, START, END

from app.pipeline.graph_state import RAGState

from app.pipeline.graph_nodes import (
    rewrite_node,
    retrieval_node,
    reranking_node,
    generation_node
)


# -----------------------------------------
# CREATE STATE GRAPH
# -----------------------------------------

workflow = StateGraph(RAGState)


# -----------------------------------------
# REGISTER NODES
# -----------------------------------------

workflow.add_node("rewrite", rewrite_node)

workflow.add_node("retrieval", retrieval_node)

workflow.add_node("reranking", reranking_node)

workflow.add_node("generation", generation_node)


# -----------------------------------------
# DEFINE EXECUTION FLOW
# -----------------------------------------

workflow.add_edge(START, "rewrite")

workflow.add_edge("rewrite", "retrieval")

workflow.add_edge("retrieval", "reranking")

workflow.add_edge("reranking", "generation")

workflow.add_edge("generation", END)


# -----------------------------------------
# COMPILE GRAPH
# -----------------------------------------

rag_graph = workflow.compile()


print("NEXORA AI LangGraph workflow compiled successfully.")
