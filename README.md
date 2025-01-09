# ms-score

## Descripción del Proyecto

**ms-score** es un servicio diseñado para calcular y gestionar puntuaciones relacionadas con ofertas de empleo, perfiles de usuarios y recomendaciones. Este microservicio utiliza algoritmos personalizados para analizar datos y generar un ranking que optimiza la correspondencia entre candidatos y ofertas de trabajo.

## Funcionalidades Principales

- **Cálculo de Puntuaciones**:
  - Asignación de puntuaciones a candidatos basadas en sus habilidades, experiencia y otras características.
  - Análisis de ofertas de empleo para calcular una relevancia relativa con respecto a perfiles disponibles.

- **Recomendaciones Personalizadas**:
  - Generación de recomendaciones de empleo para los usuarios basadas en sus puntuaciones.
  - Identificación de candidatos ideales para las ofertas de trabajo.

- **Integración con Kafka**:
  - Escucha eventos de creación o actualización de perfiles y ofertas para recalcular las puntuaciones.
  - Publicación de eventos con los resultados del cálculo de puntuación.

- **API RESTful**:
  - Endpoints para consultar las puntuaciones y recomendaciones generadas.

## Arquitectura

- **Cálculo de Puntuaciones**:
  - Algoritmos personalizados implementados para evaluar correspondencia.
  - Uso de librerías de Machine Learning (opcional) para modelos avanzados.

- **Base de Datos**:
  - PostgreSQL para almacenar las puntuaciones calculadas.
  - Modelos definidos con SQLAlchemy.

- **Mensajería**:
  - Kafka se utiliza para integrar los cálculos de puntuaciones con otros microservicios.

## Configuración

### Variables de Entorno

El proyecto requiere las siguientes variables de entorno, configuradas en un archivo `.env`:

- `DB_HOST`: Host de la base de datos.
- `DB_PORT`: Puerto de la base de datos.
- `DB_NAME`: Nombre de la base de datos.
- `DB_USER`: Usuario de la base de datos.
- `DB_PASSWORD`: Contraseña de la base de datos.
- `KAFKA_BOOTSTRAP_SERVERS`: Dirección del servidor Kafka.

### Instalación

1. Clona este repositorio:
   ```bash
   git clone <repositorio>
   cd ms-score
