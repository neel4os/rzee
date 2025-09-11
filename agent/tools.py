from datetime import datetime
from langchain_core.tools import tool

@tool
def check_time():
    """Check the current time and return a greeting based on the time of day."""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    return current_time
