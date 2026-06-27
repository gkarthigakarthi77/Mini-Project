import re
from datetime import datetime

def sanitize_input(text: str) -> str:
    return re.sub(r'[<>]', '', text)

def format_datetime(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%d %H:%M:%S')