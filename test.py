from agent.agent import graph


response = graph.invoke(
    {"messages": [{"role": "user", "content": "HI What are you doing?"}]},
    config={"configurable": {"thread_id": 1}},
)

print(response)
