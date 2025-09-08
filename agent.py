from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3


Kobold_url = "http://localhost:5001/v1"
ModelName = "modelname"


def get_system_prompt():
    with open("system_prompt.json", "r", encoding="utf-8") as f:
        system_prompt = json.load(f)
    return system_prompt["system_prompt"]


Base_System_Prompt = "\n".join(get_system_prompt())


def get_scenario():
    with open("scenario.json", "r", encoding="utf-8") as f:
        scenario = json.load(f)
    return scenario


def get_characters():
    with open("character.json", "r", encoding="utf-8") as f:
        characters = json.load(f)
    return characters


def get_preset():
    with open("preset.json", "r", encoding="utf-8") as f:
        preset = json.load(f)
    return preset


preset = get_preset()
scenario = get_scenario()
character = get_characters()
System_Prompt = f"{Base_System_Prompt}\n{str(scenario)}\n{str(character)}"
prompt_template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=System_Prompt),
        MessagesPlaceholder(variable_name="msgs"),
    ]
)


def create_kobold_client():
    return ChatOpenAI(
        base_url=Kobold_url,
        api_key="does not matter",
        max_completion_tokens=30,
        model_kwargs=preset,
    )


class State(BaseModel):
    messages: Annotated[list, add_messages]
    system_injected: bool = Field(default=True)


def chatbot(state: State, config: RunnableConfig) -> str:
    llm = create_kobold_client()
    formatted_prompt = prompt_template.invoke({"msgs": state.messages})
    return {"messages": [llm.invoke(formatted_prompt, config)]}


graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
stmemory = SqliteSaver(conn)
graph = graph_builder.compile(checkpointer=stmemory)
