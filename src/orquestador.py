"""Agente Orquestador de la Mesa de Ayuda IA - Departamento Legal, Patito S.A.

Recibe la pregunta del usuario, clasifica la intencion (via tool-calling del LLM), invoca a
uno o varios agentes especializados, y consolida una respuesta final indicando que agentes
participaron y (cuando esta disponible) que fragmentos/fuentes se usaron.
"""
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from .agente_accion import consultar_accion
from .agente_contratos import consultar_contratos
from .agente_cumplimiento import consultar_cumplimiento
from .agente_proteccion_datos import consultar_proteccion_datos
from .config import GOOGLE_API_KEY, LLM_MODEL

# Trazabilidad de la ultima consulta: que agentes participaron y con que fuentes.
_ultimo_resultado_por_agente: dict[str, dict] = {}


@tool
def invocar_agente_contratos(pregunta: str) -> str:
    """Consulta al Agente de Contratos (clausulas contractuales, tipos de contrato, plazos,
    proceso de revision y firma). Pasale la pregunta del usuario, o una sub-pregunta reformulada
    si es parte de una consulta mixta."""
    r = consultar_contratos(pregunta)
    _ultimo_resultado_por_agente["contratos"] = r
    return r["respuesta"]


@tool
def invocar_agente_proteccion_datos(pregunta: str) -> str:
    """Consulta al Agente de Proteccion de Datos (tratamiento de datos personales,
    consentimiento, derechos de los titulares, retencion/eliminacion, seguridad, brechas)."""
    r = consultar_proteccion_datos(pregunta)
    _ultimo_resultado_por_agente["proteccion_datos"] = r
    return r["respuesta"]


@tool
def invocar_agente_cumplimiento(pregunta: str) -> str:
    """Consulta al Agente de Cumplimiento Normativo (codigo de etica, conflictos de interes,
    regalos/obsequios, anticorrupcion, canal de denuncias)."""
    r = consultar_cumplimiento(pregunta)
    _ultimo_resultado_por_agente["cumplimiento"] = r
    return r["respuesta"]


@tool
def invocar_agente_accion(pregunta: str) -> str:
    """Enruta al Agente de Accion SOLO cuando el usuario pide explicitamente registrar, crear o
    guardar una solicitud de elaboracion/revision de contrato. NO usar para preguntas
    informativas sobre contratos (esas van a invocar_agente_contratos)."""
    r = consultar_accion(pregunta)
    _ultimo_resultado_por_agente["accion"] = r
    return r["respuesta"]


_llm_orquestador = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0, google_api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT_ORQUESTADOR = """Eres el Orquestador de la Mesa de Ayuda IA del Departamento Legal
de Patito S.A. NO respondes preguntas legales por tu cuenta: tu trabajo es clasificar la
intencion del usuario, invocar a los agentes especializados correctos, y consolidar sus
respuestas en una unica respuesta final clara y organizada.

AGENTES DISPONIBLES (tools):
- invocar_agente_contratos: clausulas contractuales, tipos de contrato, proceso de firma.
- invocar_agente_proteccion_datos: datos personales, consentimiento, retencion, derechos.
- invocar_agente_cumplimiento: etica, conflictos de interes, regalos, anticorrupcion.
- invocar_agente_accion: SOLO cuando el usuario pide registrar/crear una solicitud de contrato.

REGLAS:
- Si la consulta toca varios temas a la vez (ej: un contrato con un proveedor que tratara datos
  personales, mas reglas de cumplimiento aplicables), invoca TODOS los agentes relevantes y
  consolida sus respuestas en una sola respuesta final organizada por tema.
- Nunca generes contenido legal por tu cuenta: toda informacion legal debe venir de un agente
  especializado invocado como tool.
- Al final de tu respuesta, indica que agente(s) participaron.
- Si ningun agente encontro informacion suficiente, dilo explicitamente en vez de inventar.
- Si el usuario esta confirmando un registro pendiente del agente de accion (ej. dice "si,
  confirmo", "registralo"), incluye en el argumento de invocar_agente_accion TODO el contexto
  necesario: copia literalmente el id_propuesta que aparecio en la respuesta anterior de esa
  tool (formato "id_propuesta=XXXXXXXX") y menciona que el usuario confirmo. El agente de accion
  no tiene memoria propia entre llamadas, asi que si no le pasas el id_propuesta explicitamente
  en el mensaje, no va a saber a que propuesta te referis."""

agente_orquestador = create_agent(
    model=_llm_orquestador,
    tools=[
        invocar_agente_contratos,
        invocar_agente_proteccion_datos,
        invocar_agente_cumplimiento,
        invocar_agente_accion,
    ],
    system_prompt=SYSTEM_PROMPT_ORQUESTADOR,
)


def _extraer_texto(mensaje) -> str:
    """El content de un AIMessage puede ser un string simple o una lista de bloques
    (ej. [{'type': 'text', 'text': '...'}]) segun el proveedor. Esto normaliza a texto plano."""
    contenido = mensaje.content
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        partes = []
        for bloque in contenido:
            if isinstance(bloque, dict) and bloque.get("type") == "text":
                partes.append(bloque.get("text", ""))
            elif isinstance(bloque, str):
                partes.append(bloque)
        return "\n".join(partes).strip()
    return str(contenido)


def preguntar(pregunta: str, historial: list | None = None) -> dict:
    """Punto de entrada principal: recibe la pregunta del usuario y devuelve la respuesta
    consolidada junto con la trazabilidad (agentes participantes y fuentes).

    `historial` es la lista de mensajes (BaseMessage) de la conversacion hasta ahora. Pasarla es
    IMPRESCINDIBLE para flujos de varios turnos como la confirmacion del agente de accion: sin
    historial, cada pregunta arranca una conversacion nueva y el orquestador no recuerda que ya
    habia una propuesta de registro pendiente. El resultado incluye el historial actualizado
    (`historial`) para que el llamador (ej. main.py) lo guarde y lo reenvie en la siguiente
    pregunta.
    """
    _ultimo_resultado_por_agente.clear()
    mensajes = list(historial) if historial else []
    mensajes.append({"role": "user", "content": pregunta})

    resultado = agente_orquestador.invoke({"messages": mensajes})

    agentes_participantes = list(_ultimo_resultado_por_agente.keys())
    fuentes = {
        nombre: r["fuentes"]
        for nombre, r in _ultimo_resultado_por_agente.items()
        if "fuentes" in r
    }
    return {
        "respuesta": _extraer_texto(resultado["messages"][-1]),
        "agentes_participantes": agentes_participantes,
        "fuentes": fuentes,
        "historial": resultado["messages"],
    }
