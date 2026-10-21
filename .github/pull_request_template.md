## Checklist de revisión
- [ ] 1. ¿Cada criterio de aceptación tocado tiene test que lo referencia?
- [ ] 2. ¿Los tests fallan si rompo la implementación a propósito?
- [ ] 3. ¿Hay algún test omitido, marcado o con aserción vacía?
- [ ] 4. ¿El diff contiene algo fuera del alcance declarado en la spec?
- [ ] 5. ¿Alguna dependencia nueva existe, se mantiene y era necesaria?
- [ ] 6. ¿Se conserva la precisión decimal y el redondeo se aplica una sola vez, al final?
- [ ] 7. ¿La traza de auditoría se escribe en todas las ramas del código nuevo?
- [ ] 8. ¿La cobertura sube porque se cubre lógica o porque se añadió código trivial?
- [ ] 9. ¿Entiendo lo suficiente este cambio como para defenderlo ante el cliente?
> Si la respuesta a la 9 es "no", el PR no se aprueba aunque el pipeline esté en verde.