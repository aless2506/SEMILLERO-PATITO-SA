# Ejemplos de preguntas y respuestas esperadas

> Estos son ejemplos orientativos de lo que debería producir el sistema. La redacción exacta
> del LLM puede variar; lo que debe mantenerse es: **de qué agente(s) viene**, **que se base en
> los documentos**, y **que cite fuentes / diga "no encontré información suficiente" cuando
> corresponda**.

## 1. Agente de Contratos

**Pregunta:** ¿Qué cláusulas mínimas debe contener un contrato de prestación de servicios con un proveedor?

**Se espera:** el orquestador invoca solo a `invocar_agente_contratos`. La respuesta lista las
cláusulas mínimas del documento 1 (identificación de las partes, objeto, alcance/entregables,
plazo, precio, confidencialidad, protección de datos, propiedad intelectual, SLA, responsabilidad
e indemnización, terminación, resolución de controversias), citando el fragmento de origen.

---

## 2. Agente de Protección de Datos

**Pregunta:** ¿Por cuánto tiempo podemos conservar los datos personales de un cliente que canceló su cuenta?

**Se espera:** el orquestador invoca solo a `invocar_agente_proteccion_datos`. La respuesta dice
que se conservan 5 años tras la cancelación por obligaciones contables/fiscales/legales, y que
luego se eliminan o anonimizan.

---

## 3. Agente de Cumplimiento Normativo

**Pregunta:** ¿Puedo aceptar un obsequio de un proveedor durante una negociación de contrato?

**Se espera:** el orquestador invoca solo a `invocar_agente_cumplimiento`. La respuesta indica que
NO, que durante una negociación, licitación o evaluación de proveedor no se acepta ningún
obsequio sin importar su valor (regla distinta de la cortesía general de hasta USD 50).

---

## 4. Consulta mixta (orquestación multi-agente)

**Pregunta:** *Vamos a firmar un contrato con un proveedor que tratará datos personales de
nuestros clientes. ¿Qué cláusulas debe incluir el contrato, qué obligaciones de protección de
datos aplican y qué reglas de cumplimiento debo considerar?*

**Se espera:** el orquestador detecta 3 sub-intenciones e invoca:
- `invocar_agente_contratos` → cláusulas mínimas, incluida la cláusula de protección de datos
  personales cuando el proveedor trate datos.
- `invocar_agente_proteccion_datos` → obligación de firmar un acuerdo de tratamiento de datos
  con el proveedor (encargado de tratamiento), principios aplicables.
- `invocar_agente_cumplimiento` → reglas generales de ética/conflicto de interés a considerar en
  la relación con el proveedor.

La respuesta final consolida los tres bloques, indicando qué agentes participaron.

---

## 5. Pregunta fuera de alcance (control de alucinaciones)

**Pregunta:** ¿Cuál es la tasa de impuesto a la renta corporativo en Ecuador este año?

**Se espera:** ningún documento de la base cubre tributación. El agente relevante (o el
orquestador si no logra clasificarla) debe responder:
*"No encontré información suficiente en la base documental proporcionada."*
No debe inventar una tasa ni buscarla fuera de los documentos.

---

## 6. Agente de Acción (registro)

**Turno 1 — Pregunta:** Registra una solicitud de contrato de prestación de servicios con el
proveedor Servicios XYZ, objeto: soporte de redes, plazo 12 meses, monto USD 6,000, sí trata
datos personales.

**Se espera:** el orquestador invoca `invocar_agente_accion`. Como los 6 datos obligatorios están
completos, el agente llama a `preparar_solicitud_registro`, genera un `id_propuesta`, y devuelve
un resumen pidiendo confirmación explícita. **Todavía no escribe nada en el archivo.**

**Turno 2 — Pregunta:** Sí, confirmo, regístralo.

**Se espera:** el agente llama a `confirmar_registro` con el `id_propuesta` del turno anterior,
escribe la línea en `registro_solicitudes_legal.txt` con un ID único (`SOL-YYYYMMDD-xxxxxxxx`) y
fecha/hora, y confirma al usuario.

**Caso con datos incompletos — Pregunta:** Registra una solicitud de contrato con el proveedor
ABC Ltda.

**Se espera:** faltan objeto, plazo, monto y si trata datos personales. El agente **no llama** a
`preparar_solicitud_registro`; en su lugar, pide explícitamente los datos faltantes.

---

## 7. Agente Multimodal de Imagen (bonus opcional)

**Uso:** `analizar_imagen("contrato_escaneado.png", "¿Contiene las cláusulas mínimas requeridas y están firmadas todas las páginas?")`

**Se espera:** el modelo describe lo que puede leer/ver en la imagen (texto, presencia de firmas
o sellos visibles) sin inventar contenido que no sea legible, y aclara que es orientativo.
