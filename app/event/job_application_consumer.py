# job_application_consumer.py
import asyncio
import json
import logging
from typing import Dict, Any
from aiokafka import AIOKafkaConsumer

from app.config.database import get_db, async_session
from app.service.scoring_service import ScoringService

logger = logging.getLogger(__name__)


class JobApplicationEventConsumer:
    def __init__(self):
        self.consumer = AIOKafkaConsumer(
            'job-events',
            bootstrap_servers='localhost:9092',
            group_id='scoring-processor-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest'
        )
        self.scoring_service = ScoringService()

    async def start(self):
        """Inicia el consumo de eventos"""
        logger.info("Iniciando consumidor de eventos de aplicaciones de trabajo...")
        try:
            await self.consumer.start()
            logger.info("Consumidor iniciado y esperando mensajes...")

            async for message in self.consumer:
                try:
                    logger.info(f"Mensaje recibido: {message.value}")
                    await self.process_event(message.value)
                except Exception as e:
                    logger.error(f"Error procesando mensaje: {str(e)}")

        except Exception as e:
            logger.error(f"Error en el consumidor: {str(e)}")
        finally:
            await self.consumer.stop()

    async def process_event(self, event: Dict[str, Any]):
        """Procesa eventos relacionados con aplicaciones de trabajo."""
        try:
            event_type = event.get('type')

            if event_type == 'job-application-created':
                await self._handle_job_application_created(event.get('data'))
            else:
                logger.warning(f"Tipo de evento no reconocido: {event_type}")

        except Exception as e:
            logger.error(f"Error procesando evento: {str(e)}")

    async def _handle_job_application_created(self, data: Dict[str, Any]):
        """Procesa el evento `job-application-created`."""
        try:
            profile = data["profile"]
            job_offer = data["job_offer"]
            application_id = data["application_id"]
            user_id = data["user_id"]
            job_offer_id = data["job_offer_id"]

            cv_text = profile.get("about", "")

            async with async_session() as session:
                async with session.begin():  # Contexto transaccional
                    # Realizar la evaluación
                    evaluation = self.scoring_service.evaluate_cv(
                        cv_text=cv_text,
                        role=job_offer.get("title", "Unknown Role"),
                        job_application_id=application_id,
                        user_id=user_id,
                        job_offer_id=job_offer_id,
                        db=session  # Pasa la sesión asíncrona al servicio
                    )
                    logger.info(f"Evaluación guardada: {evaluation}")

        except Exception as e:
            logger.error(f"Error manejando el evento job-application-created: {str(e)}")
