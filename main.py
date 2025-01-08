from fastapi import FastAPI
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import evaluator
import logging
from app.config.database import init_db
from app.event.job_application_consumer import JobApplicationEventConsumer

app = FastAPI()

# Configurar el logger
logging.basicConfig(level=logging.INFO)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    evaluator.router
)

# Inicializa la base de datos
init_db()


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "langsmith_enabled": True
    }


@app.on_event("startup")
async def startup_event():
    """
    Evento de inicio de la aplicación.
    - Crea la tarea asíncrona para el consumidor de eventos.
    """
    try:
        # Instanciar el consumidor de eventos
        job_application_consumer = JobApplicationEventConsumer()

        # Crear las tareas asíncronas para los consumidores
        app.state.consumer_tasks = [
            asyncio.create_task(job_application_consumer.start()),
        ]

        # Manejo de errores en las tareas
        for task in app.state.consumer_tasks:
            task.add_done_callback(lambda t: handle_consumer_task_result(t))

        logging.info("Tareas de consumidores inicializadas exitosamente.")
    except Exception as e:
        logging.error(f"Error inicializando consumidores: {str(e)}")


def handle_consumer_task_result(task):
    """
    Maneja el resultado de las tareas de los consumidores.
    Si una tarea termina con error, lo registra.
    """
    try:
        task.result()
    except asyncio.CancelledError:
        logging.info("La tarea fue cancelada normalmente durante el apagado.")
    except Exception as e:
        logging.error(f"Consumer task failed with error: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento de cierre de la aplicación.
    - Cancela las tareas de los consumidores.
    """
    if hasattr(app.state, 'consumer_tasks'):
        for task in app.state.consumer_tasks:
            if not task.done():
                task.cancel()

        await asyncio.gather(*app.state.consumer_tasks, return_exceptions=True)
        logging.info("Tareas de consumidores canceladas correctamente.")


if __name__ == "__main__":
    import uvicorn

    # Ejecuta la aplicación
    uvicorn.run(app, host="0.0.0.0", port=8095, workers=2)
