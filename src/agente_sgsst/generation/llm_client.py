import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

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

    def generar_texto(self, prompt, sistema="Eres un experto consultor en SG-SST bajo normatividad colombiana."):
        """
        Genera texto utilizando el proveedor configurado.
        """
        if self.provider == "groq" and self.groq_key:
            return self._llamar_groq(prompt, sistema)
        elif self.provider == "openai" and self.openai_key:
            return self._llamar_openai(prompt, sistema)
        elif self.provider == "gemini" and self.gemini_key:
            return self._llamar_gemini(prompt, sistema)
        else:
            # Fallback inteligente si no hay llaves configuradas
            return f"""[Contenido generado automáticamente por el Agente SG-SST (Modo Simulación Inteligente)]\n\nPrompt procesado:\n{prompt[:300]}...\n\n(Para activar llamadas reales a LLM, configure GROQ_API_KEY, OPENAI_API_KEY o GEMINI_API_KEY en el archivo .env)."""

    def _llamar_groq(self, prompt, sistema):
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=60)
            res_json = response.json()
            if "choices" in res_json:
                return res_json['choices'][0]['message']['content']
            else:
                return f"Error en respuesta Groq: {json.dumps(res_json)}"
        except Exception as e:
            return f"Error en API Groq: {str(e)}"

    def _llamar_openai(self, prompt, sistema):
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error en API OpenAI: {str(e)}"

    def _llamar_gemini(self, prompt, sistema):
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(f"{sistema}\n\n{prompt}")
            return response.text
        except Exception as e:
            return f"Error en API Gemini: {str(e)}"
