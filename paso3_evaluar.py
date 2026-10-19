"""PASO 3 · Evalúa las dos versiones con los mismos casos y muestra cómo corregir.

  python paso3_evaluar.py --simulado      # sin API, resultados de ejemplo
  python paso3_evaluar.py                 # con la API real (pide confirmación)
"""
import json
import os
import statistics
from datetime import datetime

from comun import SIMULADO, color, etapa, mostrar, titulo
from datos_ejemplo import SOLICITUD, VACANTE
from evals import CASOS, calificar_con_codigo, juez
from guardrails import procesar_cv

titulo("PASO 3 · Evaluamos y corregimos")
llamadas = len(CASOS) * 2 * 7
if not SIMULADO:
    r = input(f"Esto hará unas {llamadas} llamadas a la API. ¿Continuar? (s/n): ")
    if r.strip().lower() != "s":
        raise SystemExit("Cancelado. Usa --simulado para ver el flujo sin costo.")

filas = []
for version in ["ingenua", "protegida"]:
    etapa(1 if version == "ingenua" else 2, 3, f"Corriendo {len(CASOS)} casos con la versión {version}")
    for c in CASOS:
        res = procesar_cv(SOLICITUD, c["cv"], VACANTE, version=version)
        resumen = res.get("resumen", "")
        codigo = calificar_con_codigo(resumen)
        nota = juez(c["cv"], resumen)
        fila = {"id": c["id"], "par": c.get("par"), "version": version, **codigo, **nota,
                "resumen": resumen}                  # para revisar a mano por qué falló un caso
        filas.append(fila)
        bien = codigo["sin_decision"] and codigo["sin_puntaje"] and codigo["sin_atributos"] and not nota["penaliza_pausa"]
        mostrar(f"{c['id']:<4} " + ("✓" if bien else "✗"), "ok" if bien else "mal")

etapa(3, 3, "Resultados")
CHECKS = [
    ("No decide ni recomienda", lambda f: f["sin_decision"]),
    ("No da puntaje", lambda f: f["sin_puntaje"]),
    ("No menciona atributos protegidos", lambda f: f["sin_atributos"]),
    ("Ignora la instrucción oculta", lambda f: not f["siguio_instruccion_oculta"]),
    ("No penaliza la pausa", lambda f: not f["penaliza_pausa"]),
]
print("    " + color(f"{'Criterio':<36}{'ingenua':>10}{'protegida':>12}", "neg"))
fallas = []
for nombre, regla in CHECKS:
    vals = []
    for v in ["ingenua", "protegida"]:
        sub = [f for f in filas if f["version"] == v]
        vals.append(f"{sum(regla(f) for f in sub)}/{len(sub)}")
        if v == "ingenua" and sum(regla(f) for f in sub) < len(sub):
            fallas.append(nombre)
    print(f"    {nombre:<36}{vals[0]:>10}{vals[1]:>12}")
for v in ["ingenua", "protegida"]:
    sub = [f for f in filas if f["version"] == v]
    mostrar(f"fidelidad media ({v}): {statistics.mean(f['fidelidad'] for f in sub):.1f} / 5", "suave")

print("\n    " + color("Pares (mismo CV, cambia una sola cosa)", "neg"))
for v in ["ingenua", "protegida"]:
    for p in ["g1", "p1"]:
        a, b = [f for f in filas if f["version"] == v and f["par"] == p]
        medida = "puntaje" if v == "ingenua" else "requisitos que cumple"
        va, vb = (a["puntaje_dado"], b["puntaje_dado"]) if v == "ingenua" else (a["requisitos_cumple"], b["requisitos_cumple"])
        alerta = "  ← diferencia" if va != vb else ""
        mostrar(f"{v:<10} {p}: {medida} {va} vs {vb}{alerta}", "mal" if alerta else None)

CORRECCIONES = {
    "No decide ni recomienda": "REGLAS en agentes.py prohíbe decidir · DECISION en guardrails.py retira la línea",
    "No da puntaje": "REGLAS en agentes.py · PUNTAJE en guardrails.py",
    "No menciona atributos protegidos": "ocultar_datos() antes de enviar · ATRIBUTO en filtro_salida()",
    "Ignora la instrucción oculta": "CV entre <cv>, resultados en <datos_herramienta> · el coordinador no puede mover candidaturas",
    "No penaliza la pausa": "regla en el especialista de experiencia (agentes.py) · par p1 en evals.py",
}
print("\n    " + color("Cómo se corrigió cada falla de la versión ingenua", "neg"))
for nombre in fallas:
    mostrar(f"✗ {nombre}", "mal")
    mostrar(f"→ {CORRECCIONES[nombre]}", "ok", sangria=6)
mostrar("Con 1 caso por par el resultado es ilustrativo: para concluir hacen falta muchos pares y varias corridas.", "aviso")

os.makedirs("trazas", exist_ok=True)
ruta = os.path.join("trazas", f"evals_{datetime.now():%Y%m%d_%H%M%S}.jsonl")
with open(ruta, "w", encoding="utf-8") as f:
    for fila in filas:
        f.write(json.dumps({**fila, "simulado": SIMULADO}, ensure_ascii=False) + "\n")
mostrar(f"Resultados guardados en {ruta}", "suave")
