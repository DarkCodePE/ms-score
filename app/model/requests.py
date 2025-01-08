from pydantic import BaseModel

class CVRequest(BaseModel):
    cv_text: str
    role: str
