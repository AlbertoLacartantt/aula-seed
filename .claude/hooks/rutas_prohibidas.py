"""Hook PreToolUse: bloquea la escritura en las rutas que CLAUDE.md declara prohibidas."""
import json
import sys
from fnmatch import fnmatch
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PROHIBIDAS = ["src/aula/legado/*", "manifiestos/*", ".github/workflows/*",
              "labs/*/verificar.py", "evals/dorado*"]

datos = json.load(sys.stdin)
ruta = Path(datos["tool_input"]["file_path"]).resolve()
try:
    relativa = ruta.relative_to(RAIZ).as_posix()
except ValueError:
    sys.exit(0)

for patron in PROHIBIDAS:
    if fnmatch(relativa, patron):
        print("%s es una ruta prohibida . Pide aprobacion a la persona."
              % relativa, file=sys.stderr)
        sys.exit(2)
