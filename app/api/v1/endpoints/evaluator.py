from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.model.model import JobApplicationScore
from app.model.requests import CVRequest
from app.model.responses import CVResponse
from app.service.scoring_service import ScoringService

router = APIRouter(prefix="/evaluator", tags=["evaluator"])
service = ScoringService()


@router.get("/eval", response_model=List[dict])
async def get_scores(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100
):
    """
    Obtiene la lista de evaluaciones de CVs.
    """
    scores = (
        db.query(JobApplicationScore)
        .order_by(desc(JobApplicationScore.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Convertir los resultados a diccionarios
    return [
        {
            "id": str(score.id),
            "job_application_id": score.job_application_id,
            "user_id": score.user_id,
            "job_offer_id": score.job_offer_id,
            "score": score.score,
            "reasoning": score.reasoning,
            "created_at": score.created_at.isoformat()
        }
        for score in scores
    ]


@router.get("/{score_id}")
async def get_score(score_id: str, db: Session = Depends(get_db)):
    """
    Obtiene una evaluación específica por su ID.
    """
    score = db.query(JobApplicationScore).filter(JobApplicationScore.id == score_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    return {
        "id": str(score.id),
        "job_application_id": score.job_application_id,
        "user_id": score.user_id,
        "job_offer_id": score.job_offer_id,
        "score": score.score,
        "reasoning": score.reasoning,
        "created_at": score.created_at.isoformat()
    }


@router.get("/application/{application_id}")
async def get_score_by_application(application_id: str, db: Session = Depends(get_db)):
    """
    Obtiene la evaluación para una aplicación específica.
    """
    score = (
        db.query(JobApplicationScore)
        .filter(JobApplicationScore.job_application_id == application_id)
        .first()
    )

    if not score:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    return {
        "id": str(score.id),
        "job_application_id": score.job_application_id,
        "user_id": score.user_id,
        "job_offer_id": score.job_offer_id,
        "score": score.score,
        "reasoning": score.reasoning,
        "created_at": score.created_at.isoformat()
    }


@router.post("/", response_model=CVResponse)
async def evaluate_cv(request: CVRequest):
    try:
        result = service.evaluate_cv(cv_text=request.cv_text, role=request.role)
        return CVResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")
