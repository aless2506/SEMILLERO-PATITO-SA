"""Agente de Cumplimiento Normativo.

Responde sobre codigo de etica, conflictos de interes, regalos, anticorrupcion y canal de
denuncias, usando UNICAMENTE su propia base de conocimiento embebida (03_Cumplimiento_Etica.txt).
"""
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import DATA_DIR, GOOGLE_API_KEY, LLM_MODEL, TOP_K
from .vectorstore_utils import construir_o_cargar_vectorstore

_vectordb_cumplimiento = construir_o_cargar_vectorstore(
    doc_path=str(DATA_DIR / "03_Cumplimiento_Etica.txt"),
    nombre_indice="cumplimiento",
)


@tool
def buscar_en_base_cumplimiento(consulta: str) -> str:
    """Busca fragmentos relevantes en la Guia de Cumplimiento Normativo y Codigo de Etica de
    Patito S.A. Usa esta herramienta SIEMPRE antes de responder sobre etica, conflictos de
    interes, regalos y obsequios, anticorrupcion, prevencion de lavado de activos o el canal de
    denuncias."""
    resultados = _vectordb_cumplimiento.similarity_search(consulta, k=TOP_K)
    if not resultados:
        return "NO_RESULTS"
    return "\n\n".join(
        f"[Fragmento {i} | fuente: {d.metadata.get('fuente', '03_Cumplimiento_Etica.txt')}]\n"
        f"{d.page_content}"
        for i, d in enumerate(resultados, 1)
    )


_llm_cumplimiento = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0, google_api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT_CUMPLIMIENTO = """Eres el Agente de Cumplimiento Normativo del Departamento Legal
de Patito S.A.

Respondes UNICAMENTE preguntas sobre: codigo de etica, conflictos de interes, regalos y
obsequios (incluida la regla de no aceptar obsequios de proveedores durante negociaciones),
anticorrupcion, prevencion de lavado de activos y el canal de denuncias.

REGLAS:
- SIEMPRE usa la herramienta buscar_en_base_cumplimiento antes de responder. No respondas de
  memoria.
- Basa tu respuesta UNICAMENTE en los fragmentos recuperados. No inventes montos, reglas ni
  excepciones que no esten en la base documental.
- Si los fragmentos recuperados no cubren la pregunta (o la herramienta devuelve NO_RESULTS),
  responde exactamente: "No encontre informacion suficiente en la base documental proporcionada."
- Al final de tu respuesta, indica brevemente de que fragmento(s) sacaste la informacion.
- Aclara que tu respuesta es orientativa y no sustituye la asesoria de un abogado.
- No respondas preguntas de contratos ni de proteccion de datos; esas las maneja otro agente
  especializado."""

agente_cumplimiento = create_agent(
    model=_llm_cumplimiento,
    tools=[buscar_en_base_cumplimiento],
    system_prompt=SYSTEM_PROMPT_CUMPLIMIENTO,
)


def consultar_cumplimiento(pregunta: str) -> dict:
    """Invoca al agente de cumplimiento y devuelve respuesta + fuentes usadas."""
    resultado = agente_cumplimiento.invoke({"messages": [{"role": "user", "content": pregunta}]})
    fuentes = [
        m.content[:300]
        for m in resultado["messages"]
        if type(m).__name__ == "ToolMessage" and m.name == "buscar_en_base_cumplimiento"
    ]
    return {
        "agente": "Agente de Cumplimiento Normativo",
        "respuesta": resultado["messages"][-1].content,
        "fuentes": fuentes,
    }
