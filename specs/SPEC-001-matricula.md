# SPEC-001: motor de matrícula

Versión: v1.3.0 | Estado: activa
Autor: referencia del laboratorio | Revisor: SME de plataforma

## Propósito

Decidir, para una solicitud de matrícula de un estudiante en un curso académico,
qué asignaturas se admiten, cuáles quedan en lista de espera y cuáles se rechazan,
aplicando la normativa del plan de estudios vigente en el momento de la solicitud.
La decisión debe quedar auditada con la versión de plan aplicada.

## Entradas y salidas

| Elemento | Tipo | Restricciones |
|----------|------|---------------|
| Solicitud | estudiante, curso académico, lista de códigos, momento ISO-8601 | Lista no vacía, sin duplicados |
| Expediente | registros académicos previos | Puede estar vacío (estudiante de nuevo ingreso) |
| Plan | plan versionado | El aplicado es el vigente en el momento de la solicitud |
| Ventana | inicio y fin ISO-8601 | Inclusiva en ambos extremos |
| Grupos | capacidad y ocupación por asignatura | Ausencia de grupo significa sin límite |
| Salida | Matrícula con una línea por código solicitado | Cada línea: admitida, en espera o rechazada con motivo |

## Invariantes

- INV-01: toda evaluación de solicitud escribe exactamente una entrada de auditoría con el código y la versión de plan aplicados.
- INV-02: el número de líneas de la matrícula resultante es igual al número de códigos solicitados. Nunca se pierde ni se duplica una solicitud de asignatura.
- INV-03: una matrícula en estado confirmada o posterior no puede cambiar de plan de estudios.

## Criterios de aceptación

- CA-01: dado un momento fuera de la ventana de matrícula, cuando se evalúa la solicitud, entonces se rechaza la solicitud completa con error de ventana cerrada.
- CA-02: dada una asignatura con algún prerrequisito no superado, cuando se evalúa la solicitud, entonces esa línea se rechaza indicando los prerrequisitos pendientes, sin afectar al resto de líneas.
- CA-03: dado un conjunto de asignaturas cuya suma de créditos supera el límite del plan, cuando se evalúa la solicitud, entonces se admiten en orden de solicitud hasta agotar el límite y se rechazan las restantes. Excepción: si los créditos pendientes para terminar el título son iguales o inferiores al umbral de fin de carrera, el límite efectivo pasa a ser el total pendiente.
- CA-04: dada una asignatura con el máximo de convocatorias consumidas, cuando se evalúa la solicitud, entonces esa línea se rechaza por convocatorias agotadas. Una convalidación no consume convocatoria.
- CA-05: dada una asignatura cuyo grupo está completo, cuando se evalúa la solicitud, entonces esa línea queda en lista de espera y no consume créditos del límite. El resto de la matrícula continúa.
- CA-06: dado un expediente con asignaturas convalidadas, cuando se calculan los créditos superados, entonces los créditos convalidados cuentan como superados.
- CA-07: dadas varias solicitudes concurrentes, cuando se ordenan para asignar plazas, entonces se ordenan por créditos superados de mayor a menor y, a igualdad, por momento de solicitud ascendente.
- CA-08: dada una asignatura ya superada, cuando se evalúa la solicitud, entonces esa línea se rechaza por asignatura ya superada.

## Casos límite

| Caso | Resultado esperado |
|------|--------------------|
| Solicitud en el instante exacto de inicio o de fin de ventana | Aceptada, la ventana es inclusiva |
| Estudiante de nuevo ingreso, expediente vacío | Solo se admiten asignaturas sin prerrequisitos |
| Créditos pendientes iguales al umbral de fin de carrera | Se aplica la excepción de CA-03 |
| Asignatura con grupo completo y además prerrequisito pendiente | Prevalece el rechazo por prerrequisito, no la lista de espera |
| Plan sin grupos declarados | Ninguna línea va a lista de espera |

## Fuera de alcance

Rutas: src/aula/reglas/motor.py, src/aula/dominio/, src/aula/api/app.py, tests/test_reglas_matricula.py, tests/test_api_matriculas.py, specs/SPEC-001-matricula.md

- Pago de tasas y su conciliación.
- Reserva y gestión de plazas de la lista de espera a lo largo del curso.
- Anulación de matrícula una vez confirmada.
- Convalidaciones: esta spec las consume, no las decide.
- Cálculo de la nota media, que es objeto de SPEC-002.

## Ambigüedades detectadas y resolución

| # | Ambigüedad | Resolución | Fecha |
|---|-----------|------------|-------|
| A-01 | El enunciado original decía "se rechazan las asignaturas que superen el límite" sin fijar orden. Con orden indeterminado el resultado no es reproducible | Se admiten en el orden en que aparecen en la solicitud. Recogido en CA-03 | 2026-08 |
| A-02 | No estaba definido si una convalidación consume convocatoria | No la consume. Recogido en CA-04 | 2026-08 |
| A-03 | No está definido qué transiciones de estado de la matrícula son válidas. El material solo fija INV-03 y deja fuera de alcance la anulación tras confirmar | Pendiente de validar. Propuesta implementada: SOLICITADA→VALIDADA, VALIDADA→CONFIRMADA, CONFIRMADA→EN_CURSO, EN_CURSO→CALIFICADA, CALIFICADA→CERRADA; ANULADA solo desde SOLICITADA o VALIDADA; CERRADA y ANULADA son finales; sin saltos, retrocesos ni autotransiciones. Preguntas: ¿la anulación tras confirmar está prohibida o solo fuera de esta spec? ¿VALIDADA puede volver a SOLICITADA? | 2026-10 |
| A-04 | INV-03 no precisa sobre qué estado se evalúa, qué cuenta como cambio de plan ni qué excepción prevalece si coinciden dos errores | Pendiente de validar. Propuesta implementada: se evalúa sobre el estado actual (VALIDADA→CONFIRMADA con cambio de plan se permite); pasar el mismo plan no es cambio; si la transición es inválida prevalece TransicionInvalida sobre PlanInmutable. Pregunta: ¿se debe rechazar un nuevo_plan vacío o inexistente? | 2026-10 |
| A-05 | transicionar recibe solo el código del nuevo plan, no su versión, así que no está definido cómo se actualiza version_plan_aplicada | Pendiente de resolver. Hoy solo se actualiza plan_aplicado y la versión queda la del plan anterior | 2026-10 |
| A-06 | Solo se fija que el prerrequisito prevalece sobre la lista de espera. No está definido qué motivo gana si una línea incumple varias reglas | Pendiente de validar. Propuesta implementada: no pertenece al plan → ya superada → prerrequisitos → convocatorias → grupo completo (espera) → límite de créditos. La espera va antes del límite porque no consume créditos | 2026-10 |
| A-07 | CA-03 dice "hasta agotar el límite y se rechazan las restantes", pero no aclara si una asignatura posterior más pequeña que aún cabe se admite | Pendiente de validar. Propuesta implementada: cada línea se admite si cabe en los créditos que quedan; no se corta en la primera que no cabe | 2026-10 |
| A-08 | No está definido qué hacer con un código que no pertenece al plan, ni con una lista vacía o con duplicados | Pendiente de validar. Propuesta implementada: el código ajeno al plan es una línea rechazada (respeta INV-02); lista vacía o con duplicados lanza ValueError tras escribir la auditoría (respeta INV-01) | 2026-10 |
| A-09 | No está definido el estado de la matrícula que devuelve la evaluación | Pendiente de validar. Propuesta implementada: SOLICITADA; el paso a VALIDADA es una transición posterior | 2026-10 |
| A-10 | Al ordenar solicitudes, no está definido qué hacer si un estudiante no tiene expediente | Pendiente de validar. Propuesta implementada: se trata como nuevo ingreso, con 0 créditos superados | 2026-10 |
| A-11 | El endpoint de alta no define de dónde sale el expediente del estudiante | Pendiente de validar. Propuesta implementada: almacén de expedientes en memoria, vacío al arrancar; un estudiante ausente es nuevo ingreso | 2026-10 |
| A-12 | El endpoint no define qué ventana, plan ni grupos aplicar | Pendiente de validar. Propuesta implementada: ventana fija de 2026-09-01T00:00:00 a 2026-09-30T23:59:59; plan PLAN-2024; sin grupos (sin límite de plazas) | 2026-10 |
| A-13 | El momento de la solicitud es opcional en la API y no está definido qué hacer si falta o llega con zona horaria | Pendiente de validar. Propuesta implementada: si falta se usa la hora local del servidor sin zona; si no es ISO-8601 o lleva zona horaria se responde 422 | 2026-10 |
| A-14 | No están definidas las respuestas HTTP ni qué se guarda | Pendiente de validar. Propuesta implementada: 201 con la matrícula, que se guarda en memoria por estudiante; 409 si la ventana está cerrada; 422 si la solicitud es inválida | 2026-10 |