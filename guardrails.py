"""PASO 2 · Los guardrails: cinco capas alrededor del coordinador."""
import re

import comun
from agentes import AGENTES
from orquestador import coordinar

# --- Capa 1 · Filtro de entrada: ¿esta solicitud le toca al sistema? ----------------
CLASIFICAR = {
    "name": "clasificar",
    "description": "Registra si la solicitud está dentro del alcance del asistente.",
    "input_schema": {"type": "object", "properties": {
        "permitido": {"type": "boolean"},
        "categoria": {"type": "string", "enum": ["revision_cv", "discriminacion", "privacidad", "fuera_de_alcance"]},
        "motivo": {"type": "string"}},
        "required": ["permitido", "categoria", "motivo"]},
}


def filtro_entrada(solicitud):
    r = comun.client.messages.create(
        model=comun.TRABAJADOR, max_tokens=300, tools=[CLASIFICAR],
        tool_choice={"type": "tool", "name": "clasificar"},   # obliga a responder con el esquema
        system=("Clasificas solicitudes para un asistente que resume CV contra los requisitos de una vacante. "
                "Revisar un CV es válido. Filtrar o preferir por género, edad, estado civil, maternidad, "
                "origen o discapacidad es discriminacion. Buscar redes sociales o datos fuera del CV es privacidad."),
        messages=[{"role": "user", "content": solicitud}],
    )
    return next(b.input for b in r.content if b.type == "tool_use")


# --- Capa 2 · Datos personales: se ocultan ANTES de llegar al modelo ----------------
DATOS_PERSONALES = [
    ("nombre", re.compile(r"(?im)^(nombre:\s*).+$"), r"\1[OCULTO]"),
    ("edad", re.compile(r"(?im)^((?:edad|fecha de nacimiento):\s*).+$"), r"\1[OCULTO]"),
    ("estado_civil", re.compile(r"(?im)^(estado civil:\s*).+$"), r"\1[OCULTO]"),
    ("nacionalidad", re.compile(r"(?im)^(nacionalidad:\s*).+$"), r"\1[OCULTO]"),
    ("correo", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[CORREO OCULTO]"),
    ("telefono", re.compile(r"\+?\d[\d\s-]{8,}\d"), "[TELÉFONO OCULTO]"),
]


def ocultar_datos(texto):
    encontrados = []
    for nombre, patron, reemplazo in DATOS_PERSONALES:
        if patron.search(texto):
            encontrados.append(nombre)
            texto = patron.sub(reemplazo, texto)
    return texto, encontrados


# --- Capa 3 · Delimitación: el CV va entre <cv> y los resultados entre <datos_herramienta>
#     (ver orquestador.py). Así una instrucción escondida en el CV se trata como datos.

# --- Capa 4 · Permisos: cada agente solo usa las herramientas declaradas en agentes.py
CON_EFECTOS = {"mover_a_entrevista", "enviar_respuesta"}       # siempre con aprobación humana
PERMISOS = {a.nombre: a.permisos for a in AGENTES}


def ejecutar_herramienta(agente, herramienta, aprobar=None):
    if herramienta not in PERMISOS.get(agente, set()):
        return False, f"'{herramienta}' no está permitido para el agente {agente}"
    if herramienta in CON_EFECTOS and not (aprobar and aprobar(herramienta)):
        return False, "La reclutadora no aprobó la acción"
    return True, f"[SIMULADO] {herramienta} ejecutada"


# --- Capa 5 · Filtro de salida: lo que llega a la reclutadora ------------------------
ATRIBUTO = re.compile(r"(?im)^.*\b(edad|años de edad|\d{2} años|embaraz\w*|estado civil|casad[ao]|solter[ao]|"
                      r"hij[oa]s?|maternidad|paternidad|nacionalidad)\b.*$")
DECISION = re.compile(r"(?im)^.*\b(rechaz\w*|descart\w*|no contratar|recomiendo contratar\w*|contratarl[ao]|"
                      r"la mejor opci[oó]n)\b.*$")
PUNTAJE = re.compile(r"\b\d{1,3}\s*/\s*(?:10|100)\b|\b(?:puntaje|puntuaci[oó]n|score)\b[^\n\d]{0,15}\d+", re.I)
RETIROS = [
    ("atributo_protegido", ATRIBUTO, "[LÍNEA RETIRADA: menciona un atributo protegido]"),
    ("decision", DECISION, "[LÍNEA RETIRADA: la decisión es de la reclutadora]"),
    ("puntaje", PUNTAJE, "[PUNTAJE RETIRADO]"),
]


def filtro_salida(texto):
    texto, hallazgos = ocultar_datos(texto)
    for nombre, patron, reemplazo in RETIROS:
        if patron.search(texto):
            hallazgos.append(nombre)
            texto = patron.sub(reemplazo, texto)
    return texto, hallazgos


def procesar_cv(solicitud, cv, vacante, version="protegida"):
    """Versión protegida: las cinco capas. Versión ingenua: el CV va directo al coordinador."""
    if version == "ingenua":
        resumen, traza = coordinar(cv, vacante, version="ingenua")
        return {"bloqueado": False, "resumen": resumen, "hallazgos_salida": [], "traza": traza}
    decision = filtro_entrada(solicitud)
    if not decision["permitido"]:
        return {"bloqueado": True, "categoria": decision["categoria"], "motivo": decision["motivo"]}
    cv_seguro, ocultos = ocultar_datos(cv)
    resumen, traza = coordinar(cv_seguro, vacante)
    resumen, hallazgos = filtro_salida(resumen)
    return {"bloqueado": False, "resumen": resumen, "datos_ocultos": ocultos,
            "hallazgos_salida": hallazgos, "traza": traza,
            "estado": "pendiente de revisión de la reclutadora"}
