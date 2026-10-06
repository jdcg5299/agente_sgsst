import os
import re
import time

import requests
from dotenv import load_dotenv

load_dotenv()


class LLMCallError(Exception):
    """Fallo al obtener respuesta del proveedor LLM (sin exponer JSON de error crudo)."""


_RETRY_AGAIN_RE = re.compile(r"([\d.]+)\s*seconds?", re.IGNORECASE)
_MAX_RETRY_WAIT_S = 30.0
_GROQ_RETRIES = 3


def _tiempo_reintento_groq(response) -> float:
    """Deriva el tiempo de espera (capsulado) de un 429 de Groq."""
    retry_after = response.headers.get("retry-after")
    if retry_after:
        try:
            return min(float(retry_after), _MAX_RETRY_WAIT_S)
        except ValueError:
            pass
    match = _RETRY_AGAIN_RE.search(response.text or "")
    if match:
        return min(float(match.group(1)), _MAX_RETRY_WAIT_S)
    return 20.0


class LLMClient:
    """
    Cliente unificado para conectar con modelos de lenguaje (OpenAI, Gemini, Groq).
    """

    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")

        # Determinar proveedor automáticamente si no está especificado
        default_provider = "groq" if self.groq_key else ("openai" if self.openai_key else "simulado")
        self.provider = os.getenv("LLM_PROVIDER", default_provider).lower()

    def _simular(self, prompt, sistema):
        return (
            "[Contenido generado automáticamente por el Agente SG-SST "
            "(Modo Simulación Inteligente)]\n\n"
            f"Prompt procesado:\n{prompt[:300]}...\n\n"
            "(Para activar llamadas reales a LLM, configure GROQ_API_KEY, "
            "OPENAI_API_KEY o GEMINI_API_KEY en el archivo .env)."
        )

    def generar_texto(
        self, prompt, sistema="Eres un experto consultor en SG-SST bajo normatividad colombiana."
    ):
        """
        Genera texto utilizando el proveedor configurado.

        Si el proveedor real falla (límite de tasa, timeout, error), NUNCA se
        devuelve el texto crudo del error: se genera en modo simulado y el
        detalle técnico solo se imprime en consola (no se incrusta en documentos).
        """
        try:
            if self.provider == "groq" and self.groq_key:
                return self._llamar_groq(prompt, sistema)
            if self.provider == "openai" and self.openai_key:
                return self._llamar_openai(prompt, sistema)
            if self.provider == "gemini" and self.gemini_key:
                return self._llamar_gemini(prompt, sistema)
        except LLMCallError as e:
            print(
                f"[Agente IA] AVISO: {e} Se continúa en modo simulado (el documento no contendrá el error)."
            )
        return self._simular(prompt, sistema)

    def _llamar_groq(self, prompt, sistema):
        headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
        payload = {
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
        detalle = "error desconocido"
        for intento in range(_GROQ_RETRIES):
            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60,
                )
                if response.status_code == 200:
                    contenido = response.json().get("choices", [{}])[0].get("message", {}).get("content")
                    if contenido:
                        return contenido
                    detalle = "respuesta sin contenido"
                elif response.status_code == 429:
                    detalle = "límite de tasa (429)"
                    espera = _tiempo_reintento_groq(response)
                    print(
                        f"[Agente IA] Groq alcanzó el límite de tasa; reintento en {espera:.0f}s "
                        f"(intento {intento + 1}/{_GROQ_RETRIES})."
                    )
                    time.sleep(espera)
                    continue
                else:
                    detalle = f"HTTP {response.status_code}"
            except requests.exceptions.Timeout:
                detalle = "timeout (60s)"
            except requests.exceptions.RequestException as e:
                detalle = f"error de conexión: {e}"
            break
        raise LLMCallError(
            f"Groq devolvió un error ({detalle}) y no se generó contenido. "
            "Intente nuevamente en unos segundos o active el modo simulado."
        )

    def _llamar_openai(self, prompt, sistema):
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.openai_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": sistema}, {"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMCallError(
                f"OpenAI devolvió un error y no se generó contenido: {e}. "
                "Intente nuevamente en unos segundos o active el modo simulado."
            ) from e

    def _llamar_gemini(self, prompt, sistema):
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(f"{sistema}\n\n{prompt}")
            return response.text
        except Exception as e:
            raise LLMCallError(
                f"Gemini devolvió un error y no se generó contenido: {e}. "
                "Intente nuevamente en unos segundos o active el modo simulado."
            ) from e
