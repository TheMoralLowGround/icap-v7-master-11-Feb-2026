import os
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

client = Groq(api_key=external_api_key)

# system prompt - concatenate user rule
# user conten - a sample json format.


def run_llm(system_prompt, user_content):

    if external_api_key:
        print(user_content)
        print("user_content====")
        try:
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

            print("###### Response #######")
            print(response)
            print("###### Reasoning #######")
            print(reasoning)
            print("**************")

            return response, reasoning

        except Exception as e:
            print(f"Error: {e}")
            print(f"API Key loaded: {'Yes' if external_api_key else 'No'}")
            print(f"Model name: {external_model_name}")
            return ""
    elif internal_llm_server_api:
        payload = {
            "system_prompt": system_prompt,
            "user_prompt": user_content,
            "max_tokens": int(max_completion_tokens),
            "temperature": float(temperature),
            "top_p": float(top_p),
            "reasoning_effort": reasoning_effort,
        }

        result = requests.post(internal_llm_server_api, json=payload)
        result = result.json()

        response = result["choices"][0]["message"]["content"]
        reasoning = result["choices"][0]["message"]["reasoning_content"]

        return response, reasoning
    else:
        print("No API key or local LLM server found")
        return "", ""
