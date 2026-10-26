"""Hook PreToolUse: no deja hacer git commit si la suite de tests no esta en verde."""
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
if "git commit" not in datos["tool_input"].get("command", ""):
    sys.exit(0)

tests = subprocess.run([PYTHON, "-m", "pytest", "tests/", "-q"], cwd=RAIZ,
                       capture_output=True, text=True)
if tests.returncode != 0:
    print("Los tests fallan, no se hace el commit:\n" + tests.stdout[-2000:], file=sys.stderr)
    sys.exit(2)
