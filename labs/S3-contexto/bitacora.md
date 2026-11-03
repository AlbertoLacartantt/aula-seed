# Bitacora de S3

Registra configuraciones, pruebas de permisos y resultados comparativos.

comepienzo .claude a las 15:0 finalizacion a las 16:30

Test hecho de sub agente que devuevle lo sigueinte : 

En el proyecto hay dos subagentes, definidos en .claude/agents/:

Subagente	Para qué sirve	Herramientas
implementador	Implementa un criterio de aceptación de una spec siguiendo SDD: primero el test, luego el código. No hace commits.	Read, Grep, Glob, Edit, Write, Bash
revisor	Revisa solo el diff de tu rama frente a main con la checklist de PR. Se usa antes de abrir el PR. No modifica ficheros.	Read, Grep, Glob, Bash
Visto de forma sencilla, uno escribe y el otro revisa. El revisor no tiene Edit ni Write, así que solo puede leer y opinar. Así quien revisa no puede "arreglar" el código por su cuenta y ocultar lo que ha encontrado.

Hay otros agentes que vienen con Claude Code (Explore, Plan, general-purpose…), pero no son de este proyecto.

Para usar uno, pídemelo con su nombre. Por ejemplo: "usa el revisor para revisar mi rama".



usa el subagente revisor para revisar esta rama
Agent:Revisar rama frente a main
IN
Revisa el diff de la rama actual (feat/subagentes) frente a main siguiendo tu checklist de PR. Incluye tanto los commits de la rama como, por separado, los cambios sin commitear del working tree (hay modificaciones en .aula/progreso.json y en labs/S1-rebanada-vertical/bitacora.md, labs/S2-sdd/bitacora.md, labs/S3-contexto/bitacora.md, y un PDF sin trackear "Manual del estudiante (1).pdf"). Comprueba especialmente: límite de 400 líneas de diff, conventional commits, rutas prohibidas por CLAUDE.md (src/aula/legado/, manifiestos/, .github/workflows/, labs/*/verificar.py, evals/dorado*/), dependencias nuevas, y que no haya commits de tipo "refactor". No ejecutes `python3 -m aula_cli check`. Devuelve los hallazgos ordenados por gravedad con fichero y línea, y un veredicto final (listo para PR o no), en español.
 Working in the background: Running Read S3 guide on subagents and check refactor commits · type /tasks to see its transcript
4:44 PM
He puesto en marcha el revisor. Está revisando el diff de feat/subagentes frente a main, y por separado tus cambios sin commitear: progreso.json, las tres bitácoras y el PDF.

Le he pedido que mire sobre todo:

el límite de 400 líneas de diff
que los commits sigan el formato convencional (feat:, fix:…)
que no se toque ninguna ruta prohibida del CLAUDE.md
que no haya dependencias nuevas
que no haya commits refactor
No ejecutará aula_cli check.

Cuando termine te paso lo que encuentre, ordenado de más a menos grave, y si la rama está lista para abrir el PR


De hooks : 

Pruebas a mano (pasándole el JSON al script):
- "git status" -> codigo 0. No es un commit, deja pasar sin ejecutar tests.
- "git commit -m prueba" con los tests en verde -> codigo 0. Pasa los tests y deja hacer el commit.


Limitación: solo afecta a los commits que hace el agente. Los míos, desde la terminal,
no pasan por el hook.


 COMPARACION CLAUDE CODE CON OPEN CODE MODELO BIG PICKLE 
Promt : Implementa Expediente.ultimo_intento_aprobado(codigo) en src/aula/dominio/modelos.py.
Debe devolver el registro aprobado de mayor convocatoria de esa asignatura, o None si no
tiene ninguno aprobado. Es la regla A-01 de specs/SPEC-002-expediente.md.
Escribe primero los tests en tests/test_media_expediente.py y comprueba que fallan; luego
el código. Sigue las reglas de CLAUDE.md. No hagas commit. Enséñame la salida de los tests.


Comparativa - Claude Code
Modelo: Opus 5.5
Inicio: 17:42 Fin: 17:45

Claude Code: detectó una ambigüedad que yo no había visto (empate de convocatoria entre
dos aprobados), paró y preguntó con opciones antes de implementar, citando CLAUDE.md.
No cuenta como intervención mía: la pregunta la hizo él.
Le dije que lo anotara como A-05 pendiente de validar con el mentor.

Fin: 17:45 (3 minutos). Intervenciones mías: 0.

Qué hizo:
- Leyó la spec, modelos.py y los tests antes de empezar. También leyó mis notas de
  memoria de Claude Code, así que tenía algo más de contexto que OpenCode.
- Escribió primero 2 tests (cubre: SPEC-002/CA-02) y los ejecutó: 2 failed con
  NotImplementedError. Luego el código: 12 passed en el fichero, 48 passed en la suite.
- El código coge los aprobados de la asignatura y devuelve el de mayor convocatoria
  con max(), o None si no hay. Lo he revisado y cumple A-01. El primer test pone un 9 en
  la convocatoria 2 y un 6 en la 4, y comprueba que devuelve la 4 (no la mejor nota).
- Añadió A-05 a la spec escribiendo por terminal (cat >>), no con Edit. Por ahí no pasan
  los hooks de Edit/Write: si fuera una ruta prohibida, solo lo pararía el deny... y el
  deny tampoco mira la terminal. Es el hueco de los hooks que ya sabía.
- No hizo commit ni lanzó aula_cli check. Sí ejecutó agentes.conformidad.evaluar
  porque lo pone CLAUDE.md (devuelve "evaluación privada no configurada").
- No usó los subagentes.
- Me avisó de dos cosas: que src/aula/dominio/ no está en las Rutas de SPEC-002, y
  que el hook de formato reformateó ficheros enteros.

Hook de formato: ha pasado lo que esperaba con la opción 1. El cambio real son unas
10 líneas en modelos.py y 26 en los tests, pero el diff marca 27 y 60 porque ruff
reformateó el resto de cada fichero. Diff total: 3 ficheros, 64 inserciones y 24 borrados.



Comparativa - OpenCode
Modelo:DeepSeek V4 Flash Free
Inicio: 17:52 "límite alcanzado" nada más mandar el prompt. No llegó a tocar nada.



Ciclo Orca (escritor y revisor)
Encargo: CA-09 + test de convocatorias_por_asignatura (A-04)
Inicio escritor: 9:27

Escritor: Claude Code en aula-escritor (Orca). Delegó solo en el subagente implementador,
en segundo plano, y le añadió reglas: parar si A-04 no está clara, no tocar src/, no
commit, no aula_cli check.

Inicio revisor: 9:39 

El revisor pidió permiso para buscar un Python con pytest (comando de solo lectura que
miraba también ../aula-seed). Aprobado solo esa vez (opción 1); no le di acceso permanente
a la carpeta principal ni pasé a auto mode.

Revisor: CONFORME con 2 observaciones (2m 54s).
1. Reformateo de los tests por el hook de formato -> se explica en el PR, no se toca.
2. CA-09 poco explícito con la asignatura solo convalidada -> se lo paso al escritor.
Permisos: pidió 2 comandos fuera de la allowlist (buscar el python y pytest con
.venv/Scripts/python.exe), aprobados una vez. La allowlist no cubre
".venv/Scripts/python.exe -m pytest".

Revisor 2.ª vuelta: CONFORME (44 s). Observación del CA-09 resuelta; queda la del
reformateo, explicada en el PR.
Fin del ciclo: 10:06.

