FROM python:3.11-slim

# Instalar dependencias del sistema operativo (incluyendo pandoc para conversión avanzada de documentos)
RUN apt-get update && apt-get install -y \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de requerimientos o instalar directamente
RUN pip install --no-cache-dir \
    python-docx \
    google-api-python-client \
    google-auth-oauthlib \
    requests \
    openai \
    google-generativeai

# Copiar el código fuente del proyecto
COPY . /app

# Comando por defecto para ejecutar el agente en contenedor
CMD ["python", "src/main.py"]
