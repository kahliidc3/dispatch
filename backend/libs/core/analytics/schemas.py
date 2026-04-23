from pydantic import BaseModel


class ReadinessResponse(BaseModel):
    status: str
