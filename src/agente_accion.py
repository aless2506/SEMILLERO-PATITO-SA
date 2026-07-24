"""Agente de Accion (Registro).

A diferencia de los agentes de lectura, este agente EJECUTA una accion con efecto: escribe una
solicitud de elaboracion/revision de contrato en registro_solicitudes_legal.txt.

Sistema de control (requisito obligatorio del enunciado):
  1. Valida que esten TODOS los datos obligatorios antes de registrar.
  2. Si falta algo, lo pide -> no registra hasta tenerlo completo.
  3. Genera un identificador unico + fecha/hora.
  4. Pide confirmacion explicita del usuario ANTES de escribir en el archivo.

Esto se implementa en DOS tools separadas a proposito: preparar_solicitud_registro (no escribe
nada, solo valida y arma una propuesta) y confirmar_registro (escribe, y solo si el usuario ya
confirmo). La validacion de campos obligatorios vive en codigo Python, no se le confia al LLM.
"""
import uuid
from datetime import datetime
from pathlib import Path

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import GOOGLE_API_KEY, LLM_MODEL, REGISTRO_PATH

# Propuestas preparadas pero aun no confirmadas (estado en memoria del prototipo).
# En una version productiva esto iria en una base de datos/cache con expiracion.
_propuestas_pendientes: dict[str, dict] = {}


@tool
def preparar_solicitud_registro(
    tipo_contrato: str,
    proveedor: str,
    objeto: str,
    plazo: str,
    monto: str,
    trata_datos_personales: str,
) -> str:
    """Prepara (SIN GUARDAR TODAVIA) una solicitud de elaboracion/revision de contrato.
    Requiere estos 6 datos obligatorios: tipo_contrato, proveedor (datos del proveedor/partes),
    objeto o servicio, plazo, monto, y si el proveedor tratara datos personales (si/no).
    Si el usuario no dio alguno de estos datos, NO llames esta herramienta: pidele el dato
    faltante en tu respuesta de texto. Esta herramienta NO escribe en el archivo, solo genera
    una propuesta con un id_propuesta que luego se confirma con confirmar_registro."""
    campos = {
        "tipo_contrato": tipo_contrato,
        "proveedor": proveedor,
        "objeto": objeto,
        "plazo": plazo,
        "monto": monto,
        "trata_datos_personales": trata_datos_personales,
    }
    faltantes = [nombre for nombre, valor in campos.items() if not valor or not str(valor).strip()]
    if faltantes:
        return f"FALTAN_DATOS: {', '.join(faltantes)}. Pide estos datos al usuario antes de continuar."

    id_propuesta = str(uuid.uuid4())[:8]
    _propuestas_pendientes[id_propuesta] = campos
    return (
        f"PROPUESTA DE REGISTRO (id_propuesta={id_propuesta}) - AUN NO GUARDADA:\n"
        f"  Tipo de contrato: {tipo_contrato}\n"
        f"  Proveedor: {proveedor}\n"
        f"  Objeto: {objeto}\n"
        f"  Plazo: {plazo}\n"
        f"  Monto: {monto}\n"
        f"  Trata datos personales: {trata_datos_personales}\n"
        "Muestra este resumen al usuario y pide confirmacion EXPLICITA. Si confirma, llama a "
        f"confirmar_registro con id_propuesta='{id_propuesta}'. Si corrige algun dato, vuelve a "
        "llamar a preparar_solicitud_registro con los datos corregidos."
    )


@tool
def confirmar_registro(id_propuesta: str) -> str:
    """Confirma y ESCRIBE en registro_solicitudes_legal.txt una propuesta previamente creada con
    preparar_solicitud_registro. SOLO llamar despues de que el usuario confirmo explicitamente
    (ej: dijo 'si', 'confirmo', 'correcto, registralo')."""
    campos = _propuestas_pendientes.pop(id_propuesta, None)
    if campos is None:
        return "ERROR: no existe una propuesta pendiente con ese id_propuesta. Vuelve a prepararla."

    registro_id = f"SOL-{datetime.now().strftime('%Y%m%d')}-{id_propuesta}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = (
        f"[{registro_id}] {timestamp} | "
        f"tipo_contrato={campos['tipo_contrato']} | "
        f"proveedor={campos['proveedor']} | "
        f"objeto={campos['objeto']} | "
        f"plazo={campos['plazo']} | "
        f"monto={campos['monto']} | "
        f"trata_datos_personales={campos['trata_datos_personales']}\n"
    )
    Path(REGISTRO_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRO_PATH, "a", encoding="utf-8") as f:
        f.write(linea)
    return f"Registrado con exito. ID de solicitud: {registro_id}."


_llm_accion = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0, google_api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT_ACCION = """Eres el Agente de Accion del Departamento Legal de Patito S.A.

Tu unica funcion es registrar solicitudes de elaboracion o revision de contratos, usando las
herramientas preparar_solicitud_registro y confirmar_registro.

REGLAS OBLIGATORIAS:
- Datos obligatorios antes de registrar: tipo de contrato, datos del proveedor (partes), objeto
  o servicio, plazo, monto, y si el proveedor tratara datos personales.
- Si el usuario no dio todos los datos, pidelos explicitamente en tu respuesta. NUNCA llames a
  preparar_solicitud_registro con datos vacios, inventados o adivinados.
- Cuando tengas todos los datos, llama a preparar_solicitud_registro. Esto NO guarda nada,
  solo genera una propuesta para revisar.
- Muestra la propuesta completa al usuario y pide confirmacion EXPLICITA antes de guardar.
- Solo llama a confirmar_registro si el usuario confirmo explicitamente.
- Si el mensaje que recibis incluye el texto "id_propuesta=XXXXXXXX" junto con una confirmacion
  (ej. viene del orquestador reenviando la confirmacion del usuario), llama directamente a
  confirmar_registro con ese id_propuesta -- no vuelvas a pedir los datos ni a llamar a
  preparar_solicitud_registro de nuevo.
- Nunca inventes datos que el usuario no proporciono."""

agente_accion = create_agent(
    model=_llm_accion,
    tools=[preparar_solicitud_registro, confirmar_registro],
    system_prompt=SYSTEM_PROMPT_ACCION,
)


def consultar_accion(pregunta: str, historial_previo: list | None = None) -> dict:
    """Invoca al agente de accion. Acepta un historial_previo de mensajes para soportar el flujo
    de confirmacion en 2+ turnos (preparar -> confirmar) desde una capa conversacional (CLI/API)."""
    mensajes = list(historial_previo) if historial_previo else []
    mensajes.append({"role": "user", "content": pregunta})
    resultado = agente_accion.invoke({"messages": mensajes})
    return {
        "agente": "Agente de Accion (Registro)",
        "respuesta": resultado["messages"][-1].content,
        "mensajes": resultado["messages"],
    }
