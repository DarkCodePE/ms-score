from sqlalchemy.orm import Session

from app.agent.evaluator import EvaluatorAgent
from app.model.model import JobApplicationScore


class ScoringService:
    def __init__(self):
        self.agent = EvaluatorAgent()

    def _extract_score_from_text(self, relevance_text: str) -> int:
        """Extrae el valor numérico de la puntuación del texto de relevancia."""
        import re
        try:
            # Buscar cualquier puntuación numérica en el formato "<número>/5" o precedida por "Puntuación:"
            match = re.search(r'Puntuación:\s*(\d+)|(\d+)/5', relevance_text)
            if match:
                # Extraer el grupo correspondiente al número encontrado
                return int(match.group(1) or match.group(2))
            return 0  # Si no encuentra coincidencias
        except Exception as e:
            # Manejar errores inesperados
            print(f"Error al extraer la puntuación: {e}")
            return 0

    def evaluate_cv(self,
                    cv_text: str,
                    role: str,
                    job_application_id: str,
                    user_id: str,
                    job_offer_id: str,
                    db: Session):
        try:
            # Realiza la evaluación usando el agente
            result = self.agent.evaluate(cv=cv_text, role=role)
            print(f"result agent: {result}")

            # Extraer el score numérico del texto de relevancia
            numeric_score = self._extract_score_from_text(result.relevance)

            # Crear una nueva instancia de JobApplicationScore
            evaluation = JobApplicationScore(
                job_application_id=job_application_id,
                user_id=user_id,
                job_offer_id=job_offer_id,
                score=numeric_score,  # Ahora usando el valor numérico extraído
                reasoning=result.reasoning
            )

            # Usar la sesión proporcionada
            db.add(evaluation)
            db.commit()
            db.refresh(evaluation)

            return evaluation

        except Exception as e:
            if db:
                db.rollback()  # Hacer rollback en caso de error
            raise ValueError(f"Error en el servicio de scoring: {e}")
