from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
import json
from pydantic import BaseModel
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from agent.scenario_agent import TempScenario
from typing import Optional
from agent.tools import check_time
from agent.scenario_agent import scenario_agent, get_activity
from datetime import datetime


Kobold_url = "http://localhost:5001/v1"
ModelName = "'koboldcpp/L3-8B-Stheno-v3.2-Q5_K_S-imat"


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
# scenario = get_scenario()
character = get_characters()
# System_Prompt = f"{Base_System_Prompt}\n{str(scenario)}\n{str(character)}"
prompt_template = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template("{system_prompt}"),
        MessagesPlaceholder(variable_name="msgs"),
    ]
)


def create_kobold_client():
    return ChatOpenAI(
        base_url=Kobold_url,
        api_key="does not matter",
        max_completion_tokens=preset["max_tokens"],
        frequency_penalty=preset["frequency_penalty"],
        temperature=preset["temperature"],
        top_p=preset["top_p"],
        presence_penalty=preset.get("presence_penalty", 0),
        model="gpt-4o",
        n=1,
        disable_streaming=True,
    )


llm = create_kobold_client()
chat_agent = create_react_agent(llm, tools=[])


class State(BaseModel):
    messages: Annotated[list, add_messages]
    SystemPrompt: Optional[str] = None
    scenario: Optional[str] = None
    isScenarioExpired: Optional[bool] = False
    scenarioExpiration: Optional[str] = None


def chatbot(state: State, config: RunnableConfig) -> str:
    # llm = create_kobold_client()
    print("in chatbot")
    formatted_prompt = prompt_template.invoke(
        {"msgs": state.messages, "system_prompt": state.SystemPrompt}
    )
    response = chat_agent.invoke(formatted_prompt, config)
    # return {"messages": [llm.invoke(formatted_prompt, config)]}
    return {"messages": [response["messages"][-1]]}
    # print("Response:", response)
    # return {"messages": [response]}


def scenario_injector(state: State, config: RunnableConfig) -> str:
    if (
        not state.scenarioExpiration
        or state.scenarioExpiration < datetime.now().strftime("%H:%M")
    ):
        base_scenario = get_activity()
        print("Base scenario:", base_scenario)
        # try:
        #     response = scenario_agent.invoke(
        #         {"messages": [{"role": "user", "content": "Generate a scenario"}]},
        #         config,
        #     )
        #     scenario = response["messages"][-1].content
        #     base_scenario.detail_description = scenario
        # except Exception as e:
        #     print("Error in scenario agent:", e)
        #     base_scenario.detail_description = "Amaira is going about her day."
        state.scenario = str(base_scenario.model_dump())
        state.scenarioExpiration = base_scenario.end_time if base_scenario else None
    state.SystemPrompt = f"{Base_System_Prompt}\n{state.scenario}\n{str(character)}"
    return state


def cleaning_chat(state: State, config: RunnableConfig) -> str:
    # we will delete whatever between two * in the last message
    print("in cleaning chat")
    last_message = state.messages[-1]
    last_message_content = last_message.content
    if last_message_content.count("*") >= 2:
        parts = last_message_content.split("*")
        cleaned_content = "".join(parts[::2])
        last_message.content = cleaned_content
    state.messages[-1] = last_message
    return state


graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("scenario_injector", scenario_injector)
graph_builder.add_node("cleaning_chat", cleaning_chat)
graph_builder.add_edge(START, "scenario_injector")
graph_builder.add_edge("scenario_injector", "chatbot")
#graph_builder.add_edge("chatbot", "cleaning_chat")
graph_builder.add_edge("chatbot", END)
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
stmemory = SqliteSaver(conn)
graph = graph_builder.compile(checkpointer=stmemory)
