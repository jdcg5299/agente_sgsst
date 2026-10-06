# ============================================================================
#  Agente SG-SST - Makefile
#
#  GNU Make 4.x (Windows: `choco install make`; Linux/macOS: nativo).
#  El shell no se fuerza: en Windows GNU Make usa cmd.exe y en Linux /bin/sh,
#  por lo que los targets de aquí funcionan igual en local y en CI (GitHub
#  Actions corre `make lint` y `make test`).
#
#  Uso rapido:   make help   |   make install   |   make test   |   make web
# ============================================================================

.DEFAULT_GOAL := help

.PHONY: help install sync test web cli demo lint lint-format docker-build docker-up build clean

help: ## Muestra esta ayuda
	@echo "Targets disponibles:"
	@echo "  make install       Instala dependencias (uv sync)"
	@echo "  make sync          Refresca el lockfile y re-sincroniza (uv sync --refresh)"
	@echo "  make test          Ejecuta la suite completa de pytest"
	@echo "  make web           Lanza la interfaz web Streamlit  ->  http://localhost:8501"
	@echo "  make cli           Lanza el menu CLI interactivo"
	@echo "  make demo          Regenera el diagnostico DEMO de ALEXA (no toca datos reales)"
	@echo "  make lint          Verifica estilo con ruff (check)"
	@echo "  make lint-format   Verifica formato con ruff (format --check)"
	@echo "  make docker-build  Construye la imagen Docker"
	@echo "  make docker-up     Levanta el contenedor (docker compose up --build)"
	@echo "  make build         Empaqueta el proyecto con uv build"
	@echo "  make clean         Elimina caches y artefactos de build (Windows)"

install: ## Instala dependencias del proyecto
	uv sync

sync: ## Re-sincroniza el entorno a partir del lockfile
	uv sync --refresh

test: ## Suite completa de pruebas (pytest)
	uv run pytest -q

web: ## Interfaz web Streamlit (puerto 8501, bloquea la terminal)
	uv run streamlit run app.py

cli: ## Menu CLI interactivo
	uv run python -m agente_sgsst.main

demo: ## Regenera el diagnostico DEMO (lectura del contexto real + informe demo)
	uv run python scripts/demo_diagnostico.py

lint: ## Verifica estilo con ruff
	uv run ruff check .

lint-format: ## Verifica formato con ruff
	uv run ruff format --check .

docker-build: ## Construye la imagen Docker
	docker compose build

docker-up: ## Levanta el contenedor con docker compose
	docker compose up --build

build: ## Empaqueta con uv build
	uv build

clean: ## Elimina caches y artefactos (Windows local)
	-@if exist .pytest_cache rmdir /s /q .pytest_cache 2>nul
	-@if exist .ruff_cache rmdir /s /q .ruff_cache 2>nul
	-@if exist dist rmdir /s /q dist 2>nul
	-@if exist src\agente_sgsst.egg-info rmdir /s /q src\agente_sgsst.egg-info 2>nul