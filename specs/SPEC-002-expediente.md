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

## Casos límite

| Caso | Resultado esperado |
|------|--------------------|
| Expediente vacío | Nota media 0,00, créditos 0, progreso 0,00 |
| Todas las asignaturas convalidadas | Nota media 0,00, porque ninguna cuenta para la media. Sus créditos sí cuentan como superados |
| Asignatura aprobada en convocatoria 2 y también en convocatoria 4 | Cuenta la nota de la convocatoria 4, aunque en el expediente aparezca antes la de la 2 |
| Nota con más de dos decimales en origen | Se conserva íntegra en el numerador y solo se redondea el cociente final |
| Media exactamente en el punto medio, por ejemplo 7,005 | Redondeo half-up a 7,01 |

## Fuera de alcance

Rutas: src/aula/reglas/media.py, tests/test_media_expediente.py, specs/SPEC-002-expediente.md

- Menciones, matrículas de honor y premios extraordinarios.
- Reconocimiento de créditos por actividades no académicas.
- Media de acceso a máster, que usa otra normativa.
- Decisión de convalidar, que es un proceso previo.

## Ambigüedades detectadas y resolución

| # | Ambigüedad | Resolución adoptada | Alternativas descartadas y por qué |
|---|-----------|---------------------|-------------------------------------|
| A-01 | CA-02 decía "conforme a la normativa vigente" sin decir qué nota cuenta en una asignatura repetida, ni cuál si se aprueba dos veces | Pendiente de validar con el mentor. Solo cuenta la nota con la que aprobó; si aprobó más de una vez, la de la última convocatoria. Los suspensos y no presentados no cuentan | Contar todos los intentos: castiga haber repetido. Quedarse con la mejor nota o con la primera aprobada: nadie lo ha pedido |
| A-02 | CA-03 decía "el tratamiento previsto" sin decir cómo cuenta una asignatura convalidada en la nota media | Pendiente de validar con el mentor. La convalidada no cuenta para la media, ni su nota ni sus créditos. Sus créditos sí cuentan como superados (CA-05) | Ponerle un 5,00 fijo: es inventarse una nota. Sumar su nota pero no sus créditos: la media puede salir por encima de 10 |
