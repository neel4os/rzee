import json
from langchain_openai import ChatOpenAI


Kobold_url = "http://localhost:5001/v1"
ModelName = "modelname"


def get_preset():
    with open("preset.json", "r", encoding="utf-8") as f:
        preset = json.load(f)
    return preset


def get_characters():
    with open("character.json", "r", encoding="utf-8") as f:
        characters = json.load(f)
    return characters


preset = get_preset()


def create_kobold_client(
    max_tokens: int = preset["max_tokens"], temperature: float = preset["temperature"]
):
    return ChatOpenAI(
        base_url=Kobold_url,
        api_key="does not matter",
        max_completion_tokens=max_tokens,
        frequency_penalty=preset["frequency_penalty"],
        temperature=temperature,
        top_p=preset["top_p"],
        presence_penalty=preset.get("presence_penalty", 0),
        n=1,
    )
