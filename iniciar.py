"""SET UP · Revisa tu entorno y abre la guía del taller en el navegador."""
import importlib.util
import os
import sys
import webbrowser
from pathlib import Path

print("\nRevisando tu entorno para el taller...\n")
ok = True


def revisar(cond, bien, mal):
    global ok
    print(("  ✓ " + bien) if cond else ("  ✗ " + mal))
    ok = ok and cond


revisar(sys.version_info >= (3, 10), f"Python {sys.version.split()[0]}", "Necesitas Python 3.10 o posterior")
revisar(importlib.util.find_spec("anthropic") is not None, "SDK anthropic instalado",
        "Falta el SDK: pip install -r requirements.txt")
revisar(importlib.util.find_spec("dotenv") is not None, "python-dotenv instalado",
        "Falta python-dotenv: pip install -r requirements.txt")

tiene_llave = False
if Path(".env").exists():
    tiene_llave = any(l.strip().startswith("ANTHROPIC_API_KEY=sk-ant-") and "tu-llave" not in l
                      for l in Path(".env").read_text(encoding="utf-8").splitlines())
print("  ✓ Llave de API configurada en .env (no se muestra)" if tiene_llave else
      "  ! Sin llave de API: puedes seguir todo el taller con --simulado")

guia = Path("guia/index.html").resolve()
print(f"\nAbriendo la guía: {guia}")
webbrowser.open(guia.as_uri())
print("\nListo. Siguiente: python paso1_crear_sistema.py" if ok else "\nCorrige lo marcado con ✗ y vuelve a correr python iniciar.py")
