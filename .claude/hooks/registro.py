"""Hook PostToolUse: registra cada herramienta que usa Claude Code en trazas/claude_code.jsonl.

Es la traza del agente de desarrollo, separada de la traza del sistema que construimos.
"""
import json
import os
import sys
from datetime import datetime, timezone

evento = json.load(sys.stdin)
entrada = evento.get("tool_input", {}) or {}
resumen = entrada.get("command") or entrada.get("file_path") or entrada.get("pattern") or ""

fila = {
    "hora": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "herramienta": evento.get("tool_name"),
    "detalle": str(resumen)[:200],
    "modo": evento.get("permission_mode"),
}
carpeta = os.path.join(evento.get("cwd", "."), "trazas")
os.makedirs(carpeta, exist_ok=True)
with open(os.path.join(carpeta, "claude_code.jsonl"), "a", encoding="utf-8") as f:
    f.write(json.dumps(fila, ensure_ascii=False) + "\n")
sys.exit(0)
