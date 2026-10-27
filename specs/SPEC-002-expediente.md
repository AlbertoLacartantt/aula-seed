# SPEC-002: cálculo de expediente

Versión: v0.1.0 | Estado: activa
Autor: plantilla del laboratorio | Revisor: pendiente

> Especificación de partida para S2. Antes de implementar, registra las preguntas
> que necesiten una decisión de negocio y acuerda la resolución con el mentor.

## Propósito

Calcular el estado académico de un estudiante respecto de su plan: nota media
ponderada por créditos, créditos superados y porcentaje de título completado.
De la nota media dependen procesos aguas abajo, entre ellos la ordenación para
becas, así que la reproducibilidad exacta del número es un requisito, no un detalle.

## Entradas y salidas

| Elemento | Tipo | Restricciones |
|----------|------|---------------|
| Expediente | lista de registros académicos | Un registro por convocatoria consumida o convalidación |
| Plan | plan versionado | Determina créditos por asignatura y créditos del título |
| Nota media | decimal | Exactamente dos decimales, redondeo half-up |
| Créditos superados | entero | |
| Progreso | decimal | Porcentaje con dos decimales |

## Invariantes

- INV-01: el redondeo se aplica una sola vez y al final del cálculo. Ningún valor intermedio se redondea.
- INV-02: el cálculo usa aritmética decimal, nunca coma flotante binaria.
- INV-03: el resultado es determinista: el mismo expediente y el mismo plan producen siempre el mismo número, con independencia del orden de los registros.

## Criterios de aceptación

- CA-01: dado un expediente con asignaturas aprobadas en primera convocatoria, cuando se calcula la nota media, entonces es la media de las notas ponderada por los créditos de cada asignatura, con dos decimales.
- CA-02: dada una asignatura repetida y finalmente aprobada, cuando se calcula la nota media, entonces solo cuenta la nota del aprobado de mayor convocatoria; los suspensos y no presentados no cuentan (A-01).
- CA-03: dada una asignatura convalidada, cuando se calcula la nota media, entonces no cuenta para la nota media: ni su nota ni sus créditos entran en el cálculo (A-02).
- CA-04: dado cualquier expediente, cuando se calcula la nota media, entonces el redondeo a dos decimales se aplica una sola vez sobre el cociente final y nunca sobre cada asignatura.
- CA-05: dada una asignatura convalidada, cuando se calculan los créditos superados, entonces sus créditos sí cuentan como superados.
- CA-06: dado un expediente, cuando se calcula el progreso, entonces es el porcentaje de créditos superados sobre los créditos del título, con dos decimales.
- CA-07: dado un expediente sin ninguna asignatura computable, cuando se calcula la nota media, entonces devuelve 0,00 sin error.
- CA-08: dado un estudiante, cuando se consulta su expediente en la API, entonces devuelve el resumen con la nota media y el progreso con dos decimales; si el estudiante no tiene expediente, responde 404 (A-04).
- CA-09: dado un expediente, cuando se calculan las convocatorias por asignatura, entonces solo aparecen las asignaturas que tienen algún registro, cada una con el número de convocatorias consumidas, y una convalidación no gasta convocatoria, de modo que una asignatura cuyo único registro es una convalidación aparece con 0 convocatorias (A-04).

## Casos límite

| Caso | Resultado esperado |
|------|--------------------|
| Expediente vacío | Nota media 0,00, créditos 0, progreso 0,00 |
| Todas las asignaturas convalidadas | Nota media 0,00, porque ninguna cuenta para la media. Sus créditos sí cuentan como superados |
| Asignatura aprobada en convocatoria 2 y también en convocatoria 4 | Cuenta la nota de la convocatoria 4, aunque en el expediente aparezca antes la de la 2 |
| Nota con más de dos decimales en origen | Se conserva íntegra en el numerador y solo se redondea el cociente final |
| Media exactamente en el punto medio, por ejemplo 7,005 | Redondeo half-up a 7,01 |

## Fuera de alcance

Rutas: src/aula/reglas/media.py, src/aula/api/app.py, tests/test_media_expediente.py, tests/test_api_expedientes.py, specs/SPEC-002-expediente.md

- Menciones, matrículas de honor y premios extraordinarios.
- Reconocimiento de créditos por actividades no académicas.
- Media de acceso a máster, que usa otra normativa.
- Decisión de convalidar, que es un proceso previo.

## Ambigüedades detectadas y resolución

| # | Ambigüedad | Resolución adoptada | Alternativas descartadas y por qué |
|---|-----------|---------------------|-------------------------------------|
| A-01 | CA-02 decía "conforme a la normativa vigente" sin decir qué nota cuenta en una asignatura repetida, ni cuál si se aprueba dos veces | Pendiente de validar con el mentor. Solo cuenta la nota con la que aprobó; si aprobó más de una vez, la de la última convocatoria. Los suspensos y no presentados no cuentan | Contar todos los intentos: castiga haber repetido. Quedarse con la mejor nota o con la primera aprobada: nadie lo ha pedido |
| A-02 | CA-03 decía "el tratamiento previsto" sin decir cómo cuenta una asignatura convalidada en la nota media | Pendiente de validar con el mentor. La convalidada no cuenta para la media, ni su nota ni sus créditos. Sus créditos sí cuentan como superados (CA-05) | Ponerle un 5,00 fijo: es inventarse una nota. Sumar su nota pero no sus créditos: la media puede salir por encima de 10 |
| A-03 | La tabla de salidas dice que el progreso va con dos decimales, pero no dice cómo se redondea | Pendiente de validar con el mentor. Se redondea igual que la nota media: si queda justo en la mitad, hacia arriba (3,125 % da 3,13 %) | Redondear hacia abajo o al par más cercano: la nota media ya redondea hacia arriba, y usar dos formas distintas en el mismo expediente confunde |
| A-04 | La spec no dice qué devuelve el resumen del expediente ni cómo se cuentan las convocatorias de cada asignatura | Pendiente de validar con el mentor. El resumen devuelve el estudiante, la nota media, los créditos superados, el progreso y las convocatorias de cada asignatura. Solo salen las asignaturas que tienen algún registro, y una convalidación no gasta convocatoria. En la API, la nota media y el progreso van como texto ("8.20") para no perder los dos decimales; los expedientes son los que guarda la API en memoria (A-11 de SPEC-001) y un estudiante sin expediente da 404 | Sacar todas las asignaturas del plan aunque no tengan registros: llena la respuesta de ceros que no aportan nada. Contar la convalidación como convocatoria: no es un examen, y el modelo ya no la cuenta (`convocatorias_consumidas`) |
