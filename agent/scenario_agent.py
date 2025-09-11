from pydantic import BaseModel
import json
from datetime import datetime
from util import create_kobold_client, get_characters
from langgraph.prebuilt import create_react_agent
from typing import Optional


class Scenario(BaseModel):
    description: str
    detail_description: Optional[str] = None
    category: str
    location: str
    activity_name: str
    start_time: str
    end_time: str


# class ScenarioTimeline(BaseModel):
#     previous: Scenario
#     current: Scenario
#     future: Scenario


class TempScenario(BaseModel):
    time: str
    situation: str


def get_activity(current_time: str = None) -> Optional[Scenario]:
    """
    Get the activity based on the current time.
    To generate a scenario this shall be used
    """
    # check current time is a timestamp HH:MM, if not get current time
    try:
        if current_time:
            print("Parsing provided time:", current_time)
            current_time = datetime.strptime(current_time, "%H:%M")
    except Exception as e:
        print("Error parsing time:", e)
        current_time = datetime.now().strftime("%H:%M")
    # read chores.json
    print("Getting activity for time:", current_time)
    if not current_time:
        print("No valid time provided, using current time.")
        current_time = datetime.now().strftime("%H:%M")
    print("Current time:", current_time)
    with open("chores.json", "r", encoding="utf-8") as f:
        chores = json.load(f)
    # get current day of week
    day_of_week = datetime.now().strftime("%A").lower()
    # figure out its weekday or weekend
    if day_of_week in ["saturday", "sunday"]:
        day_type = "weekends"
    else:
        day_type = "weekdays"
    # get the schedule for that day type
    schedule = chores["daily_schedule"][day_type]["schedule"]
    # get current time

    current_activity = None
    # find the scheduled activity for the current time
    for activity in schedule:
        if activity["start_time"] <= current_time <= activity["end_time"]:
            current_activity = activity
            break

    # # previous and next activity based on current activity
    # if current_activity:
    #     current_index = schedule.index(current_activity)
    #     previous_activity = schedule[current_index - 1] if current_index > 0 else None
    #     next_activity = (
    #         schedule[current_index + 1] if current_index < len(schedule) - 1 else None
    #     )
    # else:
    #     previous_activity = None
    #     next_activity = None
    # print(previous_activity, current_activity, next_activity)
    # timeline = ScenarioTimeline(
    #     previous=Scenario(previous_activity),
    #     current=Scenario(current_activity),
    #     future=Scenario(next_activity),
    # )
    return Scenario.model_validate(current_activity) if current_activity else None


def get_prompt():
    return "You are a scenario generator. You should call get_activity() function without any argument to get the current activity.Based on the response from get_activity(), generate a detailed scenario description for Amaira.Make sure the scenario is immersive and engaging and fits the activity context and within 200 characters."


llm = create_kobold_client(max_tokens=200, temperature=1.1)
scenario_agent = create_react_agent(
    llm,
    tools=[get_activity],
    prompt=get_prompt() + str(get_characters()),
    response_format=Scenario,
)

# if __name__ == "__main__":
#     activity = get_activity()
#     print(activity)
#     print(activity.model_dump_json(indent=4))
