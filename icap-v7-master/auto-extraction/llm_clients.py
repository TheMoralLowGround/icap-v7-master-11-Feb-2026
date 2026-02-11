import os
import threading
from dotenv import load_dotenv
from groq import Groq
import requests

load_dotenv()

temperature = os.getenv("TEMPERATURE", 1)
top_p = os.getenv("TOP_P", 1)
max_completion_tokens = os.getenv("MAX_COMPLETION_TOKENS", 50000)
reasoning_effort = os.getenv("REASONING_EFFORT", "medium")

external_api_key = os.getenv("GROQ_API_KEY", None)
external_model_name = os.getenv("GROQ_MODEL_NAME", None)
internal_llm_server_api = os.getenv("LOCAL_LLM_SERVER_API", None)

# Timeouts for vLLM HTTP calls (seconds). Connection reuse + timeouts reduce
# latency when OpenShift -> Azure VM and avoid indefinite stalls.
LLM_CONNECT_TIMEOUT = int(os.getenv("LLM_CONNECT_TIMEOUT", "30"))
LLM_READ_TIMEOUT = int(os.getenv("LLM_READ_TIMEOUT", "600"))

_thread_local = threading.local()


def _get_llm_session():
    """Return a thread-local requests.Session for vLLM to reuse TCP connections."""
    if not hasattr(_thread_local, "session") or _thread_local.session is None:
        _thread_local.session = requests.Session()
    return _thread_local.session


def run_llm(system_prompt, user_content):
    if external_api_key:
        try:
            client = Groq(api_key=external_api_key)
            completion = client.chat.completions.create(
                model=external_model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=float(temperature),
                max_completion_tokens=int(max_completion_tokens),
                top_p=float(top_p),
                reasoning_effort=reasoning_effort,
                stream=False,
                stop=None,
            )
            response = completion.choices[0].message.content
            reasoning = completion.choices[0].message.reasoning
            return response, reasoning
        except Exception as e:
            print(f"Error: {e}")
            print(f"API Key loaded: {'Yes' if external_api_key else 'No'}")
            print(f"Model name: {external_model_name}")
            return "", ""
    elif internal_llm_server_api:
        payload = {
            "system_prompt": system_prompt,
            "user_prompt": user_content,
            "max_tokens": int(max_completion_tokens),
            "temperature": float(temperature),
            "top_p": float(top_p),
            "reasoning_effort": reasoning_effort,
        }
        try:
            session = _get_llm_session()
            result = session.post(
                internal_llm_server_api,
                json=payload,
                timeout=(LLM_CONNECT_TIMEOUT, LLM_READ_TIMEOUT),
            )
            result.raise_for_status()
            result = result.json()
        except requests.RequestException as e:
            print(f"vLLM request error: {e}")
            return "", ""
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print(system_prompt)
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        response = result["choices"][0]["message"]["content"]
        reasoning = result["choices"][0]["message"].get("reasoning_content", "")
        return response, reasoning
    else:
        print("No API key or local LLM server found")
        return "", ""
