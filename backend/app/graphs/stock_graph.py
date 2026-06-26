from langgraph.graph import (
    StateGraph,
    END
)

from graphs.state import (
    StockState
)

from graphs.nodes import (
    technical_node,
    news_node,
    risk_node,
    rf_prediction_node,
    xgb_prediction_node,
    lstm_prediction_node,
    final_node
)

graph = StateGraph(
    StockState
)

graph.add_node(
    "technical",
    technical_node
)

graph.add_node(
    "news",
    news_node
)

graph.add_node(
    "risk",
    risk_node
)

graph.add_node(
    "final",
    final_node
)

graph.set_entry_point(
    "technical"
)

graph.add_edge(
    "technical",
    "news"
)

graph.add_edge(
    "news",
    "risk"
)

graph.add_node(
    "rf_prediction",
    rf_prediction_node
)

graph.add_node(
    "xgb_prediction",
    xgb_prediction_node
)

graph.add_node(
    "lstm_prediction",
    lstm_prediction_node
)

graph.add_edge(
    "risk",
    "rf_prediction"
)

graph.add_edge(
    "rf_prediction",
    "xgb_prediction"
)

graph.add_edge(
    "xgb_prediction",
    "lstm_prediction"
)

graph.add_edge(
    "lstm_prediction",
    "final"
)

stock_graph = graph.compile()