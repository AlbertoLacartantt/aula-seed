"""Hook PostToolUse: formatea con ruff el fichero Python que acaba de escribir el agente."""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PYTHON = sys.executable
for candidato in (RAIZ / ".venv" / "Scripts" / "python.exe", RAIZ / ".venv" / "bin" / "python"):
    if candidato.exists():
        PYTHON = str(candidato)

datos = json.load(sys.stdin)
fichero = datos["tool_input"]["file_path"]
if fichero.endswith(".py"):
    subprocess.run([PYTHON, "-m", "ruff", "format", "--line-length", "100", fichero],
                   cwd=RAIZ, capture_output=True)
