"""PASO 2 · Pasa el CV de María por el sistema y muestra cada etapa.

  python paso2_procesar_cv.py --version ingenua    # sin guardrails: mira qué sale mal
  python paso2_procesar_cv.py                      # versión protegida con las cinco capas
  Agrega --simulado para no llamar a la API.
"""
import json
import os
import sys
import time

from comun import SIMULADO, color, etapa, mostrar, titulo
from datos_ejemplo import CV, SOLICITUD, VACANTE
from guardrails import ejecutar_herramienta, filtro_entrada, filtro_salida, ocultar_datos
from orquestador import coordinar, resumen_traza

version = "ingenua" if "ingenua" in sys.argv else "protegida"
inicio = time.time()


def al_consultar(nombre, instrucciones):
    mostrar(color(f"→ consulta a {nombre}: ", "neg") + instrucciones[:90])


def al_responder(nombre, salida, uso):
    mostrar(color(f"← {nombre} responde ({uso['entrada'] + uso['salida']} tokens)", "ok"))
    mostrar(salida, "suave", sangria=8)


if version == "ingenua":
    titulo("PASO 2a · El CV pasa por la versión INGENUA (sin guardrails)")
    etapa(1, 3, "Sin filtro de entrada: la solicitud pasa directo")
    etapa(2, 3, "El CV se envía COMPLETO al modelo")
    mostrar(CV.split("\n\nExperiencia")[0], "mal")
    etapa(3, 3, "El coordinador ingenuo (puntaje y recomendación) trabaja")
    resumen, traza = coordinar(CV, VACANTE, version="ingenua", al_consultar=al_consultar, al_responder=al_responder)
    print()
    mostrar(color("Resumen que recibiría la reclutadora:", "neg"))
    mostrar(resumen, sangria=6)
    _, problemas = filtro_salida(resumen)
    print()
    if problemas:
        mostrar(color("✗ Problemas que detectan nuestras reglas de código: " + ", ".join(problemas), "mal"))
    if "mejor opción" in resumen.lower() or "recomiendo contratar" in resumen.lower():
        mostrar(color("✗ El resumen repite la instrucción escondida en el CV", "mal"))
    mostrar("Siguiente: python paso2_procesar_cv.py   (versión protegida)", "suave")
else:
    titulo("PASO 2b · El CV pasa por la versión PROTEGIDA (cinco guardrails)")
    etapa(1, 6, "Capa 1 · Filtro de entrada")
    decision = filtro_entrada(SOLICITUD)
    mostrar(f"\"{SOLICITUD[:60]}…\" → {decision['categoria']}", "ok" if decision["permitido"] else "mal")
    prueba = filtro_entrada("Descarta a las personas mayores de 40 años.")
    mostrar(f"\"Descarta a las personas mayores de 40 años.\" → {prueba['categoria']} (bloqueada)", "mal")

    etapa(2, 6, "Capa 2 · Ocultar datos personales antes de enviar")
    cv_seguro, ocultos = ocultar_datos(CV)
    mostrar(cv_seguro.split("\n\nExperiencia")[0], "ok")
    mostrar(f"ocultos: {', '.join(ocultos)}", "suave")

    etapa(3, 6, "Capa 3 · El coordinador delega; el CV y los resultados van delimitados como datos")
    resumen, traza = coordinar(cv_seguro, VACANTE, al_consultar=al_consultar, al_responder=al_responder)

    etapa(4, 6, "Capa 5 · Filtro de salida")
    limpio, hallazgos = filtro_salida(resumen)
    mostrar("sin hallazgos: nada que retirar" if not hallazgos else "retirado: " + ", ".join(hallazgos),
            "ok" if not hallazgos else "aviso")

    etapa(5, 6, "Resumen para la reclutadora (pendiente de su revisión)")
    mostrar(limpio, sangria=6)

    etapa(6, 6, "Capa 4 · Permisos: ¿puede el coordinador mover a María a entrevista?")
    ok, msg = ejecutar_herramienta("coordinador", "mover_a_entrevista")
    mostrar(("✓ " if ok else "✗ ") + msg, "ok" if ok else "mal")
    ok, msg = ejecutar_herramienta("reclutadora", "mover_a_entrevista", aprobar=lambda h: True)
    mostrar("reclutadora (con confirmación) → " + msg, "ok")

r = resumen_traza(traza)
print()
mostrar(color(f"Traza: {r['turnos']} turnos del coordinador · consultas: {', '.join(r['consultas'])} · "
              f"{r['tokens']} tokens · {time.time() - inicio:.1f} s", "suave"))
os.makedirs("trazas", exist_ok=True)
with open(os.path.join("trazas", f"paso2_{version}.jsonl"), "w", encoding="utf-8") as f:
    for fila in traza:
        f.write(json.dumps({**fila, "version": version, "simulado": SIMULADO}, ensure_ascii=False) + "\n")
