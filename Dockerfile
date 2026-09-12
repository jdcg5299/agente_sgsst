FROM python:3.11-slim

# Instalar dependencias del sistema operativo (incluyendo pandoc para conversión avanzada de documentos)
RUN apt-get update && apt-get install -y \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar el código fuente del proyecto
COPY . /app

# Instalar el paquete (entrada CLI: agente-sgsst). Como el proyecto usa uv_build
# como backend, pip resuelve el build system declarado en pyproject.toml.
RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir \
    python-docx \
    google-api-python-client \
    google-auth-oauthlib \
    requests \
    openai \
    google-generativeai

# Comando por defecto para ejecutar el agente en contenedor
CMD ["python", "-m", "agente_sgsst.main"]
