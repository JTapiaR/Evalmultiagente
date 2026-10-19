"""Hook PreToolUse: bloquea comandos de shell que intenten tocar el archivo .env.

Claude Code envía el evento como JSON por stdin. Salir con código 2 bloquea la acción
y el texto de stderr se le muestra a Claude como motivo.
"""
import json
import re
import sys

evento = json.load(sys.stdin)
comando = evento.get("tool_input", {}).get("command", "")

sin_ejemplo = comando.replace(".env.ejemplo", "")   # la plantilla sí se puede leer
if re.search(r"(^|[\s/\"'=<>|;&])\.env(\b|$)", sin_ejemplo):
    print("Bloqueado por guardia.py: los comandos no pueden leer ni modificar .env.", file=sys.stderr)
    sys.exit(2)

sys.exit(0)
