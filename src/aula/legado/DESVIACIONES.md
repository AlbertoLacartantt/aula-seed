# Desviaciones del refactor del legado

Diferencias entre `calculadora_expediente_v1.py` y `calculadora_expediente.py` sobre el
corpus de 500 expedientes (`tests/test_equivalencia_legado.py`). El resto de resultados
es identico.

## D-01. Nota media

- **Categoria:** aritmetica, de `float` a `Decimal`.
- **Causa:** el legado calcula en `float`; el refactor en `Decimal` con redondeo half-up
  (invariante 2 de CLAUDE.md).
- **Efecto aguas abajo:** 29 de 500 medias suben 0,01. La ordenacion de becas cambia para
  57 estudiantes, como maximo 4 puestos.

## D-02. Progreso

- **Categoria:** redondeo, de al par a half-up.
- **Causa:** `round()` redondea la mitad al par (3,125 da 3,12); el refactor la redondea
  hacia arriba (3,13), como SPEC-002 (A-03).
- **Efecto aguas abajo:** 61 de 500 progresos suben 0,01. No afecta a la media ni a las
  becas.

## Pendiente 

El que no se cuenten los creditos de una asignatura convalidada para el calculo de la media en el denominador se mantiene por el momento . 

El redondeo se aplica por asignatura, lo que contradice el invariante 1 de CLAUDE.md.
Redondear solo al final cambiaria 39 de 500 medias.
