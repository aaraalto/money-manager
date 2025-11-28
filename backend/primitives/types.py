from datetime import date
from pydantic import BaseModel

class TimeSeriesPoint(BaseModel):
    date: date
    value: float
    context: str = ""

