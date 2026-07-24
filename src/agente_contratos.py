"""Agente de Contratos.

Responde sobre clausulas estandar, tipos de contrato, plazos y proceso de revision/firma,
usando UNICAMENTE su propia base de conocimiento embebida (01_Clausulas_Contractuales.txt).
"""
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import DATA_DIR, GOOGLE_API_KEY, LLM_MODEL, TOP_K
from .vectorstore_utils import construir_o_cargar_vectorstore

_vectordb_contratos = construir_o_cargar_vectorstore(
    doc_path=str(DATA_DIR / "01_Clausulas_Contractuales.txt"),
    nombre_indice="contratos",
)


@tool
def buscar_en_base_contratos(consulta: str) -> str:
    """Busca fragmentos relevantes en el Manual de Clausulas Contractuales Estandar de Patito S.A.
    Usa esta herramienta SIEMPRE antes de responder sobre tipos de contrato, clausulas minimas
    de un contrato, o el proceso de revision y firma."""
    resultados = _vectordb_contratos.similarity_search(consulta, k=TOP_K)
    if not resultados:
        return "NO_RESULTS"
    return "\n\n".join(
        f"[Fragmento {i} | fuente: {d.metadata.get('fuente', '01_Clausulas_Contractuales.txt')}]\n"
        f"{d.page_content}"
        for i, d in enumerate(resultados, 1)
    )


_llm_contratos = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0, google_api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT_CONTRATOS = """Eres el Agente de Contratos del Departamento Legal de Patito S.A.

Respondes UNICAMENTE preguntas sobre: tipos de contrato, clausulas minimas, plazos, condiciones
de renovacion y el proceso de revision y firma de contratos.

REGLAS:
- SIEMPRE usa la herramienta buscar_en_base_contratos antes de responder. No respondas de memoria.
- Basa tu respuesta UNICAMENTE en los fragmentos recuperados. No inventes clausulas ni procesos
  que no esten en la base documental.
- Si los fragmentos recuperados no cubren la pregunta (o la herramienta devuelve NO_RESULTS),
  responde exactamente: "No encontre informacion suficiente en la base documental proporcionada."
- Al final de tu respuesta, indica brevemente de que fragmento(s) sacaste la informacion.
- Aclara que tu respuesta es orientativa y no sustituye la asesoria de un abogado.
- No respondas preguntas de proteccion de datos ni de cumplimiento normativo; esas las maneja
  otro agente especializado."""

agente_contratos = create_agent(
    model=_llm_contratos,
    tools=[buscar_en_base_contratos],
    system_prompt=SYSTEM_PROMPT_CONTRATOS,
)


def consultar_contratos(pregunta: str) -> dict:
    """Invoca al agente de contratos y devuelve respuesta + fuentes usadas (trazabilidad)."""
    resultado = agente_contratos.invoke({"messages": [{"role": "user", "content": pregunta}]})
    fuentes = [
        m.content[:300]
        for m in resultado["messages"]
        if type(m).__name__ == "ToolMessage" and m.name == "buscar_en_base_contratos"
    ]
    return {
        "agente": "Agente de Contratos",
        "respuesta": resultado["messages"][-1].content,
        "fuentes": fuentes,
    }
