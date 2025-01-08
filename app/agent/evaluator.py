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

        # Prompt para la relevancia
        self.relevance_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Eres un asistente encargado de evaluar CVs. Evalúa el perfil resumido para el rol {role}."
                ),
                (
                    "human",
                    "Evalúa este perfil y proporciona una puntuación de idoneidad del 1 al 5, incluyendo un razonamiento breve:\n\n{summary}"
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
                    "Información a formatear:\n\nRole: {role}\n\nSummary: {summary}\n\nRelevance: {relevance}"
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
                {"role": RunnablePassthrough(), "summary": self.summary_chain, "relevance": self.relevance_chain}
                | self.format_prompt
                | {"formatted_output": self.llm | self.parser}
        )

    def evaluate(self, cv: str, role: str):
        try:
            result = self.format_chain.invoke({"cv": cv, "role": role})
            return result["formatted_output"]
        except Exception as e:
            raise ValueError(f"Error durante la evaluación: {e}")
