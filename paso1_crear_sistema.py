"""PASO 1 · Crea el sistema multiagente y muestra su arquitectura. No llama a la API."""
from agentes import AGENTES, COORDINADOR, ESPECIALISTAS, HERRAMIENTA_DELEGAR
from comun import color, etapa, mostrar, pausa, titulo

titulo("PASO 1 · Creamos el sistema multiagente")

etapa(1, 4, "Arquitectura: orquestador–trabajadores con paralelización")
mostrar("""
                 ┌──────────────┐
  CV + vacante → │ COORDINADOR  │ → resumen → RECLUTADORA (decide)
                 └──────┬───────┘
          consulta y recibe respuesta (en paralelo)
          ┌─────────────┼──────────────┐
    HABILIDADES     EXPERIENCIA    CONSISTENCIA""".strip("\n"), "suave")

etapa(2, 4, "Agentes declarados en agentes.py")
for a in AGENTES:
    pausa(0.3)
    tipo = "persona" if a.modelo is None else a.modelo
    print("    " + color(f"● {a.nombre:<13}", "ok") + color(f"[{tipo}]", "suave"))
    mostrar(f"rol: {a.rol}", sangria=6)
    mostrar(f"permisos: {', '.join(sorted(a.permisos))}", "suave", sangria=6)
    if a.herramientas:
        mostrar(f"herramientas: {', '.join(a.herramientas)}", "suave", sangria=6)

etapa(3, 4, "La herramienta que conecta al coordinador con los especialistas")
mostrar(f"nombre: {HERRAMIENTA_DELEGAR['name']}")
mostrar(f"especialistas permitidos (enum): {HERRAMIENTA_DELEGAR['input_schema']['properties']['especialista']['enum']}")
mostrar("el especialista NO ve la conversación: el coordinador le escribe sus instrucciones", "aviso")

etapa(4, 4, "Sistema creado")
mostrar(f"1 coordinador ({COORDINADOR.modelo}) · {len(ESPECIALISTAS)} especialistas · 1 persona que decide", "ok")
mostrar("Siguiente: python paso2_procesar_cv.py --version ingenua", "suave")
