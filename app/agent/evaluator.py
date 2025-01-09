from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

from app.model.responses import CVResponse

load_dotenv()


class EvaluatorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        # Parser para formatear la salida final
        self.parser = PydanticOutputParser(pydantic_object=CVResponse)

        # Prompt para el resumen
        self.summary_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Eres un asistente útil que resume CVs para solicitantes de empleo. Actualmente estás trabajando en un rol de {role}."
                ),
                ("human", "Por favor, resume este CV para mí:\n\n{cv}")
            ]
        )

        META_PROMPT_REASONING = """
        Evalúa el perfil resumido de un CV para el rol específico proporcionado, asignando una puntuación de idoneidad entre 1 y 5 e incluyendo un razonamiento detallado.

        - Considera la experiencia laboral, habilidades y logros del candidato en relación con los requisitos del rol.
        - Incluye aspectos relevantes como educación, certificaciones y competencias técnicas en el análisis.
        
        # Steps
        
        1. Revisa la descripción del rol {role} y sus requisitos clave.
        2. Analiza el perfil resumido del CV del candidato considerando experiencia relevante, habilidades, logros, educación y certificaciones.
        3. Basándote en el análisis, evalúa cómo se alinean estas características del candidato con el rol específico.
        4. Proporciona un razonamiento detallado de la evaluación, explicando cómo cada aspecto del perfil del candidato coincide con las necesidades del rol.
        5. Incluye los puntos a favor y en contra de cada aspecto del candidato respecto al rol para una evaluación más objetiva.
        6. Analiza de manera paso a paso y muestra en cadena de pensamiento cómo llegas a la conclusión de la idoneidad.
        7. Asigna una puntuación de idoneidad del 1 al 5, asegurando que el puntaje refleja la importancia de los años de experiencia, educación y certificaciones en el contexto del rol.
        
        # Output Format
        
        - **Razonamiento Detallado**: Un párrafo explicativo que describe cómo encajan las características del candidato con el rol, incluyendo puntos a favor y en contra.
        - **Puntuación de Idoneidad**: Un número entero entre 1 y 5, donde 1 indica poca idoneidad y 5 indica alta idoneidad, teniendo en cuenta una alineación efectiva entre la oferta y las habilidades del candidato.
        
        # Examples
        
        **Entrada:**
        - Descripción del rol: "Gerente de Proyectos TI"
        - Perfil Resumido del CV: "Profesional con 10 años de experiencia en gestión de proyectos tecnológicos, habilidades en SCRUM, PMP certificado, lideró implementación de sistemas ERP..."
        
        **Salida:**
        - Razonamiento Detallado: "El candidato tiene una experiencia fuerte en gestión de proyectos tecnológicos y cuenta con certificaciones relevantes como SCRUM y PMP, lo que le otorga una ventaja significativa para el rol de Gerente de Proyectos TI. Además, su experiencia liderando la implementación de sistemas ERP se alinea perfectamente con las necesidades del rol. Sin embargo, no se menciona experiencia específica en la industria financiera que es un requisito preferente para este puesto."
        - Puntuación de Idoneidad: 5, destacando la manera en que las habilidades y logros del candidato coinciden con los requisitos del puesto y cómo sus certificaciones y trayectoria profesional influyen en su idoneidad para el puesto, pese a la falta de experiencia en la industria financiera.
        """.strip()

        HUMAN_PROMPT = """
               Evalúa el perfil proporcionado y asigna una puntuación de idoneidad del 1 al 5. Incluir un razonamiento breve que justifique la puntuación otorgada.

                # Steps
                
                1. Analiza la información del perfil proporcionado en {summary}.
                2. Identifica los aspectos del perfil que son relevantes para determinar su idoneidad.
                3. Considera tanto las fortalezas como las debilidades del perfil.
                4. Utiliza esta información para determinar una puntuación de idoneidad del 1 al 5.
                5. Escribe un razonamiento breve que explique la puntuación asignada.
                
                # Output Format
                
                Una puntuación de idoneidad seguida de un razonamiento breve. El formato debe ser:
                
                - Puntuación: [1-5]
                - Razonamiento: [Breve explicación que justifique la puntuación dada]
                
                # Examples
                
                Example 1:
                
                - Perfil: "Ingeniero de software con 5 años de experiencia en desarrollo web y experiencia limitada en gestión de equipos."
                - Puntuación: 4
                - Razonamiento: "El perfil muestra una sólida experiencia técnica relevante, pero carece de habilidades avanzadas de gestión que se requerirían para una posición de liderazgo."
                
                Example 2:
                
                - Perfil: "Reciente graduado en ciencias de la computación con excelentes habilidades de comunicación, pero sin experiencia profesional previa."
                - Puntuación: 3
                - Razonamiento: "El perfil tiene habilidades comunicativas destacadas y una base educativa relevante, pero la falta de experiencia profesional podría ser una desventaja en roles más avanzados."
                
                # Notes
                
                - Considera diferentes áreas de relevancia según el contexto del rol o tarea para la evaluación.
                - Mantén los razonamientos concisos y directos, centrándote en los puntos clave.
                - Asegúrate de que la puntuación refleje una evaluación equilibrada del perfil.
                """.strip()

        # Prompt para la relevancia
        self.relevance_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    META_PROMPT_REASONING
                ),
                (
                    "human",
                    HUMAN_PROMPT
                ),
            ]
        )

        # Prompt para el formateo final
        self.format_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Toma la siguiente información y formatea la salida en el esquema proporcionado. La salida debe estar en formato JSON:\n{format_instructions}"
                ),
                (
                    "human",
                    "Información a formatear:\n\nRole: {role}\n\nSummary: {summary}\n\nRelevance: {relevance}\n\nReasoning: {reasoning}"
                ),
            ]
        ).partial(format_instructions=self.parser.get_format_instructions())

        # Paso 1: Resumen del CV
        self.summary_chain = (
                {"role": RunnablePassthrough(), "cv": RunnablePassthrough()}
                | self.summary_prompt
                | {"summary": self.llm | StrOutputParser()}
        )

        # Paso 2: Evaluación de relevancia
        self.relevance_chain = (
                {"summary": self.summary_chain, "role": RunnablePassthrough()}
                | self.relevance_prompt
                | {"relevance": self.llm | StrOutputParser()}
        )

        # Paso 3: Formateo final
        self.format_chain = (
                {"role": RunnablePassthrough(), "summary": self.summary_chain, "relevance": self.relevance_chain, "reasoning": self.relevance_chain}
                | self.format_prompt
                | {"formatted_output": self.llm | self.parser}
        )

    def evaluate(self, cv: str, role: str):
        try:
            result = self.format_chain.invoke({"cv": cv, "role": role})
            return result["formatted_output"]
        except Exception as e:
            raise ValueError(f"Error durante la evaluación: {e}")
