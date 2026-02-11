import os
import asyncio
from dotenv import load_dotenv
from groq import Groq
import requests

from core.title_classfication_v2.utils.logger import get_logger

logger = get_logger("llm_clients")

load_dotenv()

temperature = os.getenv("TEMPERATURE",0.3)
top_p = os.getenv("TOP_P",1)
max_completion_tokens = os.getenv("MAX_COMPLETION_TOKENS",50000)
reasoning_effort = os.getenv("REASONING_EFFORT","medium")

external_api_key = os.getenv("GROQ_API_KEY",None)
external_model_name = os.getenv("GROQ_MODEL_NAME",None)
internal_llm_server_api = os.getenv("LOCAL_LLM_SERVER_API",None)


def run_llm(system_prompt,user_content):

    if external_api_key:
        try:
            client = Groq(api_key=external_api_key)
            completion = client.chat.completions.create(
                model=external_model_name, 
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ],
                temperature=float(temperature),
                max_completion_tokens=int(max_completion_tokens),
                top_p=float(top_p),
                reasoning_effort=reasoning_effort,
                stream=False,
                stop=None)
            
            response = completion.choices[0].message.content
            reasoning  = completion.choices[0].message.reasoning
            
            return response, reasoning
        
        except Exception as e:
            logger.error(f"Error: {e}")
            return "",""
    elif internal_llm_server_api:
        try:
            payload = {
                "system_prompt": system_prompt,
                "user_prompt": user_content,
                "max_tokens": int(max_completion_tokens),
                "temperature": float(temperature),
                "top_p": float(top_p),
                "reasoning_effort":reasoning_effort
            }

            result = requests.post(internal_llm_server_api, json=payload)
            result = result.json()

            response = result["choices"][0]["message"]["content"]
            reasoning = result["choices"][0]["message"]["reasoning_content"]
            
            return response, reasoning
        
        except Exception as e:
            logger.error(f"Error: {e}")
            return "",""
    else:
        logger.error("No API key or local LLM server found")
        return "", ""

async def run_llm_async(system_prompt, user_content):
    """Async wrapper for run_llm to enable concurrent execution"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_llm, system_prompt, user_content)