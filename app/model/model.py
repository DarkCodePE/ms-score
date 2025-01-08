from langchain_core.pydantic_v1 import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from uuid import uuid4

from app.config.base import Base


class CVResponse(BaseModel):
    role: str = Field(..., description="The role being evaluated.")
    summary: str = Field(..., description="The summary of the CV.")
    relevance: str = Field(
        ..., description="The relevance of the CV for the given role, including a score and reasoning."
    )


class JobApplicationScore(Base):
    __tablename__ = "job_application_scores"
    __table_args__ = {"schema": "public"}

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    job_application_id = Column(String, nullable=False)  # Relación con JobApplication
    user_id = Column(String, nullable=False)  # ID del perfil evaluado
    job_offer_id = Column(String, nullable=False)  # ID de la oferta evaluada
    score = Column(Integer, nullable=False)  # Puntuación de idoneidad
    reasoning = Column(String, nullable=True)  # Razonamiento del puntaje
    created_at = Column(DateTime, default=datetime.utcnow)
