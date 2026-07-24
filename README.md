# PROYECTO FINAL DEL SEMILLERO
# INTEGRANTES: ALESSANDRO MAURICIO VALENCIA CONGA - ARIANNA LISSETTE COBOS MERCHAN - CARLOS ARMANDO TITO ORELLANA






# Mesa de Ayuda IA — Departamento Legal, Patito S.A.

Prototipo funcional (no productivo) del proyecto final del Semillero de Inteligencia Artificial:
una mesa de ayuda con agentes LangChain especializados que responden preguntas legales internas
usando RAG sobre una base documental ficticia, más un agente orquestador y un agente de acción.

> Las respuestas del sistema son **orientativas** y no sustituyen la asesoría de un abogado.

ENLACE DE VIDEO:https://drive.google.com/file/d/19OsXsYbOOGZChD3BrCUTQhhPd-fggp11/view?usp=sharing
## 1. Arquitectura

```
                          ┌────────────────────────┐
                Usuario → │   Agente Orquestador    │ → Respuesta consolidada
                          │  (clasifica intencion,  │
                          │   invoca 1+ agentes,    │
                          │   consolida respuesta)  │
                          └───────────┬─────────────┘
                                      │ (tools = "invocar_agente_X")
        ┌─────────────────┬──────────┼──────────────┬─────────────────┐
        ▼                 ▼          ▼               ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌──────────────────┐
│ Agente         │ │ Agente        │ │ Agente        │ │ Agente de      │ │ Agente Multimodal │
│ Contratos      │ │ Proteccion    │ │ Cumplimiento  │ │ Accion         │ │ de Imagen (bonus) │
│ (RAG)          │ │ de Datos (RAG)│ │ Normativo(RAG)│ │ (registro)     │ │                    │
├───────────────┤ ├───────────────┤ ├───────────────┤ ├───────────────┤ ├──────────────────┤
│ retriever tool │ │ retriever tool│ │ retriever tool│ │ preparar_      │ │ Gemini Vision      │
│ → Chroma       │ │ → Chroma      │ │ → Chroma      │ │ solicitud_     │ │ (llamada directa,  │
│ "contratos"    │ │ "proteccion_  │ │ "cumplimiento"│ │ registro +     │ │ sin tools)         │
│                │ │ datos"        │ │               │ │ confirmar_     │ │                    │
│                │ │               │ │               │ │ registro       │ │                    │
└───────┬────────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └──────────────────┘
        │                  │                 │                 │
        ▼                  ▼                 ▼                 ▼
 01_Clausulas_      02_Proteccion_    03_Cumplimiento_   registro_solicitudes_
 Contractuales.txt  Datos.txt         Etica.txt          legal.txt (se genera al usar el agente)
```

Cada agente de lectura tiene **su propio índice vectorial** (`vectorstores/contratos/`,
`vectorstores/proteccion_datos/`, `vectorstores/cumplimiento/`), generado con
`GoogleGenerativeAIEmbeddings`, y **no comparte** vector store con los otros — así, cada agente
solo puede recuperar información de su propia base documental, tal como exige el enunciado.

## 2. Estructura del repositorio

```
patito_legal_ai/
├── main.py                        # CLI de entrada
├── build_indexes.py                # script reproducible para generar embeddings
├── requirements.txt
├── .env.example
├── ejemplos_preguntas.md           # preguntas de prueba, incluida una mixta
├── data/                           # base documental ficticia (input, no se modifica)
│   ├── 01_Clausulas_Contractuales.txt
│   ├── 02_Proteccion_Datos.txt
│   └── 03_Cumplimiento_Etica.txt
├── src/
│   ├── config.py                   # variables de entorno, rutas, parametros RAG
│   ├── vectorstore_utils.py        # construir/cargar indices Chroma (compartido)
│   ├── agente_contratos.py         # agente RAG 1
│   ├── agente_proteccion_datos.py  # agente RAG 2
│   ├── agente_cumplimiento.py      # agente RAG 3
│   ├── agente_accion.py            # agente de accion (registro) — obligatorio
│   ├── agente_multimodal.py        # agente multimodal de imagen — bonus opcional
│   └── orquestador.py              # clasifica intencion, invoca agentes, consolida
├── vectorstores/                   # (se genera al ejecutar) indices por agente
└── registro_solicitudes_legal.txt  # (se genera al usar el agente de accion)
```

## 3. Requisitos

- Python 3.10+
- Una API Key de Google Gemini gratuita: https://aistudio.google.com/apikey
>  **Antes de ejecutar:** este proyecto necesita tu propia API Key de Google Gemini.
> Copiá `.env.example` a `.env` y completá tu `GOOGLE_API_KEY`
> (gratis en https://aistudio.google.com/apikey). Ver sección 4 más abajo.
## 4. Instalación y ejecución
EJECUTAR TODO ESTE PROCESO EN LA TERMINAL.
```bash
# 1. Clonar / entrar al proyecto
cd patito_legal_ai

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar credenciales
cp .env.example .env
# Editar .env y pegar tu GOOGLE_API_KEY

# 5. (Opcional pero recomendado) Generar los indices vectoriales de antemano
python build_indexes.py

# 6. Ejecutar la mesa de ayuda (CLI)
python main.py
```

Si saltás el paso 5, cada agente genera su índice automáticamente la primera vez que se importa
(la primera pregunta tarda un poco más). El paso 5 lo separa como script reproducible tal como
pide el enunciado ("script o proceso reproducible que genere los embeddings e índices").

### Ejemplo de sesión

```
>>> Tu pregunta: ¿Qué cláusulas mínimas debe contener un contrato de prestación de servicios con un proveedor?

>>> Respuesta:
Según el Manual de Cláusulas Contractuales Estándar, un contrato de prestación de servicios
debe incluir al menos: identificación de las partes, objeto del contrato, alcance y entregables,
plazo/vigencia, precio y forma de pago, obligaciones de cada parte, confidencialidad, protección
de datos (cuando aplique), propiedad intelectual, niveles de servicio, responsabilidad e
indemnización, causales de terminación, y resolución de controversias/ley aplicable.
[Fuente: 01_Clausulas_Contractuales.txt]
Esta respuesta es orientativa y no sustituye la asesoría de un abogado.

>>> Agentes participantes: contratos
>>> Fuentes consultadas (trazabilidad):
    - contratos: 1 fragmento(s) recuperado(s)
```

### Uso del agente multimodal (bonus, fuera del CLI)

```python
from src.agente_multimodal import analizar_imagen

resultado = analizar_imagen("ruta/a/contrato_escaneado.png",
                             "¿Contiene las clausulas minimas y estan firmadas todas las paginas?")
print(resultado["respuesta"])
```

## 5. Decisiones técnicas y trade-offs

- **Modelo LLM:** `gemini-3.1-flash-lite` por defecto (configurable en `.env`). Se eligió la
  variante "lite" en vez de `gemini-3.5-flash` porque el nivel gratuito de esta última tiene una
  cuota muy ajustada (20 solicitudes/día en las pruebas), insuficiente para una arquitectura
  multi-agente donde una sola pregunta mixta puede disparar 8-12 llamadas al LLM (orquestador +
  varios agentes, cada uno con su propio tool-calling). `gemini-3.1-flash-lite` tiene una cuota
  gratuita bastante más generosa y es además más rápido, a costa de algo de calidad de
  razonamiento — un trade-off razonable para un prototipo.
- **Embeddings:** `models/gemini-embedding-001` de Gemini. (Nota: el proyecto originalmente usaba
  `text-embedding-004`, pero Google lo deprecó el 14 de enero de 2026; `gemini-embedding-001` es
  el reemplazo recomendado y mantiene la misma interfaz de LangChain — `embed_documents` usa
  automáticamente `RETRIEVAL_DOCUMENT` y `embed_query` usa `RETRIEVAL_QUERY` por defecto).
- **Vector store:** Chroma, persistido en disco por agente. Se eligió sobre FAISS porque
  `langchain-chroma` maneja la persistencia (`persist_directory`) de forma más simple para un
  prototipo con múltiples índices independientes, sin necesitar guardar/cargar archivos de
  índice manualmente.
- **Chunking:** `chunk_size=800`, `chunk_overlap=120`, con `RecursiveCharacterTextSplitter`.
  Los documentos fuente son cortos (secciones numeradas de 1-2 páginas); un chunk de 800
  caracteres típicamente captura una sección completa (ej. toda la sección de "Regalos y
  Obsequios") sin fragmentarla a la mitad, y el overlap evita perder contexto en los bordes.
- **`top_k=4`:** con documentos tan cortos, 4 fragmentos son suficientes para cubrir cualquier
  pregunta razonable sin diluir el contexto del LLM con ruido.
- **Orquestador vía tool-calling (no un router por reglas):** se optó por dejar que el LLM
  orquestador decida qué agente(s) invocar usando tools, en vez de un clasificador de intención
  separado. Esto simplifica el código y maneja naturalmente las consultas mixtas (el modelo
  puede llamar a varias tools en una misma respuesta), a costa de una llamada extra al LLM
  (el orquestador) antes de llegar a los agentes especializados.
- **Agente de acción con 2 tools separadas (`preparar_` / `confirmar_`)** en vez de una sola:
  fuerza estructuralmente el flujo de confirmación exigido por el enunciado — el LLM no puede
  "saltarse" la confirmación porque `confirmar_registro` requiere un `id_propuesta` que solo
  existe si `preparar_solicitud_registro` ya validó que todos los campos obligatorios estaban
  presentes. La validación de campos vive en código Python, no se le confía al LLM.
- **Agente multimodal simplificado (bonus):** se implementó como una llamada directa a Gemini
  Vision (sin loop de tools) porque el caso de uso — analizar una imagen y responder — no
  requiere razonamiento multi-paso. El agente de acción es el que cubre el requisito obligatorio
  de "al menos un agente adicional".
- **Cada agente de lectura usa su propio `ChatGoogleGenerativeAI`** en vez de compartir una
  instancia global: facilita cambiar el modelo de un agente puntual (ej. usar un modelo más
  grande solo para el orquestador) sin tocar el resto.

## 6. Control de alucinaciones y respuesta segura

- Cada agente de lectura tiene una regla explícita en su `system_prompt`: si la tool de
  recuperación no encuentra nada relevante (`NO_RESULTS`) o los fragmentos no cubren la
  pregunta, debe responder literalmente *"No encontré información suficiente en la base
  documental proporcionada."* en vez de inventar.
- Cada agente está instruido para **no responder temas fuera de su dominio** (ej. el agente de
  contratos no responde preguntas de cumplimiento), delegando esa separación al orquestador.
- El agente de acción nunca inventa datos: si el LLM intentara llamar a
  `preparar_solicitud_registro` con un campo vacío, la validación en Python lo rechaza y
  devuelve qué falta, sin registrar nada.

## 7. Trazabilidad

`orquestador.preguntar()` devuelve, además de la respuesta:
- `agentes_participantes`: lista de agentes invocados en esa consulta.
- `fuentes`: por cada agente de lectura que participó, los fragmentos (con su archivo de origen)
  que se usaron para responder.

Esto permite auditar, para cualquier respuesta, exactamente qué agente y qué fragmento de qué
documento la originó.

## 8. Manejo de permisos por documento/agente (propuesta)

Como cada agente tiene su propio índice vectorial aislado, extender el control de acceso es
directo: se podría añadir un campo `roles_permitidos` en `config.py` por agente, y en el
orquestador verificar el rol del usuario (pasado como parámetro a `preguntar()`) antes de
permitir invocar `invocar_agente_X`. Por ejemplo, el agente de acción (que escribe registros)
podría restringirse a usuarios con rol "abogado_junior" o superior, mientras que los 3 agentes de
lectura quedan abiertos a todo el departamento Legal.

## 9. Riesgos y mejoras futuras

**Riesgos (prototipo, no producción):**
- Sin autenticación ni control de acceso: cualquiera que corra el CLI puede consultar y
  registrar solicitudes.
- El estado de "propuestas pendientes" del agente de acción vive en memoria (`dict` en Python):
  se pierde si el proceso se reinicia, y no escala a múltiples usuarios/procesos concurrentes.
- Sin rate limiting ni control de costos: cada pregunta mixta puede disparar 3-4 llamadas al LLM
  (orquestador + cada agente invocado); en producción esto necesita monitoreo de tokens/costo.
- El chunking fijo (800/120) fue calibrado para estos 3 documentos cortos; con documentos legales
  reales (mucho más largos y con estructura jerárquica compleja) probablemente necesitaría
  chunking jerárquico o por sección en vez de por caracteres.
- No hay manejo de duplicados en el registro de solicitudes más allá del ID único por propuesta.
- El agente multimodal no valida el tipo/tamaño de archivo antes de codificarlo en base64.

**Mejoras futuras:**
- Reemplazar el estado en memoria del agente de acción por una base de datos (ej. SQLite, como
  en el Taller 7) para persistencia y concurrencia real.
- Agregar logging estructurado sin datos sensibles (ej. loggear `agentes_participantes` y
  latencia, pero no el contenido completo de preguntas si pueden incluir datos personales).
- Instrumentar con Arize Phoenix (como en el Taller 7) para observabilidad de costos, latencia
  y trazas multi-agente en producción.
- Exponer el orquestador vía FastAPI para consumo desde una interfaz web real.
- Añadir un juez LLM (rúbrica de factualidad/completitud) para evaluar continuamente la calidad
  de las respuestas RAG, igual que en el Taller 7.

## 10. Manejo de secretos

`GOOGLE_API_KEY` y cualquier otro secreto se leen exclusivamente desde variables de entorno
(`.env`, no versionado — solo se versiona `.env.example` sin valores reales). Ningún archivo de
código contiene la key hardcodeada.

## 12. Solución de problemas comunes

- **`404 NOT_FOUND` con un modelo de embeddings o de chat:** Google retira modelos con relativa
  frecuencia. Revisá https://ai.google.dev/gemini-api/docs/deprecations por el reemplazo vigente
  y actualizá `LLM_MODEL` / `EMBEDDING_MODEL` en tu `.env`.
- **`429 RESOURCE_EXHAUSTED` con `limit: 0`:** no es que se acabó tu cuota, es que ese modelo ya
  no tiene cupo asignado en el nivel gratuito (normalmente porque fue retirado). Cambiá de modelo.
- **`429 RESOURCE_EXHAUSTED` con un `limit` mayor a 0 (ej. `limit: 20`):** ahí sí es cuota real
  agotada. Los modelos "Flash" completos (`gemini-3.5-flash`) tienen cuotas gratuitas ajustadas;
  `gemini-3.1-flash-lite` suele tener una cuota diaria bastante más generosa. La cuota (RPD)
  resetea a medianoche hora del Pacífico de EE. UU.
- **Recuerda:** cada pregunta mixta invoca al orquestador + varios agentes, cada uno con su propio
  tool-calling — eso son varias llamadas al LLM por pregunta, no una sola. Tenelo en cuenta al
  estimar cuántas preguntas podés hacer con tu cuota diaria.

## 13. Alcance

Este es un **prototipo funcional**, no una solución productiva: falta autenticación, manejo de
concurrencia robusto, y pruebas automatizadas exhaustivas. El objetivo es evidenciar el manejo
de RAG multi-agente con LangChain y Google Gemini, la orquestación entre agentes, y un sistema de
control (validación + confirmación) para el agente de acción — no reemplazar asesoría legal real.
