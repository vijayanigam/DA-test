from pydantic import BaseModel


class timeRange(BaseModel):
    start_time: int
    end_time: int



