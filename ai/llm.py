# src/ai/llm.py
from __future__ import annotations
import os, random, functools
import openai                       # ← importa primero

# ------------------------------------------------------------------  
# 1) Clave de OpenAI
# ------------------------------------------------------------------  
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("No se ha encontrado OPENAI_API_KEY.")

# ------------------------------------------------------------------  
# 2) Prompt base estilo Daxter
# ------------------------------------------------------------------  
SYSTEM_PROMPT = (
    "Eres Daxter (Jak and Daxter). "
    "Hablas en castellano, sarcástico y divertido. "
    "Respuestas cortas (≤25 palabras) y en segunda persona. "
    "Estás dentro de unas gafas inteligentes."
)

def _chat(user_prompt: str, temp: float = 0.8, max_tokens: int = 60) -> str:
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=temp,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

# ------------------------------------------------------------------  
# 3) Funciones públicas
# ------------------------------------------------------------------  
def responder_libre(prompt_usuario: str) -> str:
    """Cualquier frase libre del usuario."""
    return _chat(prompt_usuario)

def saludo_boot()  -> str: return _chat("Di una frase mientras arranco los sensores")
def saludo_listo() -> str: return _chat("Di una frase cuando todo esté listo")
def ack_wake()     -> str: return _chat(random.choice([
    "Confírmame que has escuchado la wake word",
    "Responde al usuario tras Hey colega"
]))
def sin_objetos()  -> str: return _chat("No se ha detectado nada")
def describe(objs: list[str]) -> str:
    return _chat(f"He visto estos objetos: {', '.join(objs)}")

# ------------------------------------------------------------------  
# 4) (Opcional) Pequeña caché para prompts repetidos
# ------------------------------------------------------------------  
@functools.lru_cache(maxsize=256)
def cached_describe(key: str) -> str:
    # key es "obj1|obj2|..."
    return describe(key.split("|"))
