# Etapa 1: instala las dependencias en un entorno virtual aislado.
FROM python:3.11-slim AS construccion

WORKDIR /app  #Fija la caroeta de trabajo

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Etapa 2: imagen final, solo con el entorno instalado y el codigo.
FROM python:3.11-slim

WORKDIR /app

COPY --from=construccion /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1   #Imprime lo que salga de la app en los logs inmediatamente 

COPY src/ ./src/
COPY datos/ ./datos/

RUN useradd --create-home aula && chown -R aula /app
USER aula

EXPOSE 8000

CMD python -m uvicorn aula.api.app:app --host 0.0.0.0 --port 8000
