"""El bucle del orquestador: el coordinador delega en especialistas con tool use."""
import comun
from agentes import COORDINADOR, ESPECIALISTAS, HERRAMIENTA_DELEGAR, SYSTEM_INGENUO


def especialista(nombre, instrucciones, cv, version="protegida"):
    agente = ESPECIALISTAS[nombre]
    system = agente.system if version == "protegida" else agente.rol
    r = comun.client.messages.create(
        model=agente.modelo, max_tokens=800, system=system,
        messages=[{"role": "user", "content": f"{instrucciones}\n\n<cv>\n{cv}\n</cv>"}],
    )
    return comun.texto_de(r), comun.uso_de(r)


def coordinar(cv, vacante, version="protegida", max_turnos=6, al_consultar=None, al_responder=None):
    """Devuelve (resumen, traza). Los callbacks permiten mostrar cada paso en pantalla."""
    system = COORDINADOR.system if version == "protegida" else SYSTEM_INGENUO
    mensajes = [{"role": "user", "content": f"<vacante>\n{vacante}\n</vacante>\n\n<cv>\n{cv}\n</cv>"}]
    traza = []
    for turno in range(max_turnos):                  # tope: nunca más de 6 vueltas
        r = comun.client.messages.create(
            model=COORDINADOR.modelo, max_tokens=1500, system=system,
            tools=[HERRAMIENTA_DELEGAR], messages=mensajes,
        )
        mensajes.append({"role": "assistant", "content": r.content})
        traza.append({"agente": "coordinador", "turno": turno, "stop": r.stop_reason, "uso": comun.uso_de(r)})

        if r.stop_reason != "tool_use":              # ya no pidió especialistas: es el resumen final
            return comun.texto_de(r), traza

        resultados = []
        for b in r.content:                          # responde CADA consulta del turno
            if b.type != "tool_use":
                continue
            nombre = b.input.get("especialista")
            if nombre not in ESPECIALISTAS:          # solo especialistas declarados en agentes.py
                resultados.append({"type": "tool_result", "tool_use_id": b.id, "is_error": True,
                                   "content": f"Especialista desconocido: {nombre}"})
                continue
            if al_consultar:
                al_consultar(nombre, b.input.get("instrucciones", ""))
            salida, uso = especialista(nombre, b.input.get("instrucciones", ""), cv, version)
            if al_responder:
                al_responder(nombre, salida, uso)
            traza.append({"agente": nombre, "uso": uso})
            contenido = (f"<datos_herramienta>\n{salida}\n</datos_herramienta>"   # datos, no órdenes
                         if version == "protegida" else salida)
            resultados.append({"type": "tool_result", "tool_use_id": b.id, "content": contenido})
        mensajes.append({"role": "user", "content": resultados})

    raise RuntimeError("Se agotó el presupuesto de turnos")


def resumen_traza(traza):
    return {
        "turnos": sum(1 for t in traza if t["agente"] == "coordinador"),
        "consultas": [t["agente"] for t in traza if t["agente"] != "coordinador"],
        "tokens": sum(t["uso"]["entrada"] + t["uso"]["salida"] for t in traza),
    }
