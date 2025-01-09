from typing import Optional

from pydantic import BaseModel


class CVResponse(BaseModel):
    role: str
    summary: str
    relevance: str
    reasoning: str
