"""Configuración compartida: cliente de la API (real o simulado), modelos y utilidades de pantalla."""
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()                                   # lee ANTHROPIC_API_KEY desde .env

# Modo simulado: respuestas de ejemplo, sin llamar a la API ni gastar saldo
SIMULADO = "--simulado" in sys.argv or os.getenv("TALLER_SIMULADO") == "1"
RAPIDO = "--rapido" in sys.argv

if SIMULADO:
    from simulado import ClienteSimulado
    client = ClienteSimulado()
else:
    import anthropic
    client = anthropic.Anthropic()

ORQUESTADOR = "claude-sonnet-5-5"   # coordinador: planifica y redacta
TRABAJADOR = "claude-haiku-5-5"     # especialistas y clasificadores
JUEZ = "claude-sonnet-5-5"          # evalúa los resúmenes


def texto_de(respuesta):
    """Une todos los bloques de texto de una respuesta."""
    return "".join(b.text for b in respuesta.content if b.type == "text")


def uso_de(respuesta):
    """Tokens de una llamada, listos para guardar en la traza."""
    return {"entrada": respuesta.usage.input_tokens, "salida": respuesta.usage.output_tokens}


# --- Utilidades para mostrar el avance en pantalla -------------------------------
if os.name == "nt":
    os.system("")                               # activa colores ANSI en Windows 10+
_COLOR = sys.stdout.isatty()
COLORES = {"titulo": "1;34", "ok": "32", "mal": "31", "aviso": "33", "suave": "90", "neg": "1"}


def color(texto, tipo):
    return f"\033[{COLORES[tipo]}m{texto}\033[0m" if _COLOR else texto


def pausa(segundos=0.5):
    if not RAPIDO:
        time.sleep(segundos)


def titulo(texto):
    print("\n" + color("═" * 70, "titulo"))
    print(color(texto, "titulo"))
    print(color("═" * 70, "titulo"))
    if SIMULADO:
        print(color("Modo simulado: respuestas de ejemplo, sin llamadas a la API.", "aviso"))


def etapa(n, total, texto):
    pausa(0.6)
    print("\n" + color(f"[{n}/{total}] {texto}", "neg"))


def mostrar(texto, tipo=None, sangria=4):
    for linea in str(texto).splitlines() or [""]:
        print(" " * sangria + (color(linea, tipo) if tipo else linea))
    pausa(0.15)
