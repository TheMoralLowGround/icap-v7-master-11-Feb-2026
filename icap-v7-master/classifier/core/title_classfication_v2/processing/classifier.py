from langchain_core.output_parsers import PydanticOutputParser
from pydantic import ValidationError

from core.title_classfication_v2.schemas.models import ClassificationResponse
from core.title_classfication_v2.utils.llm_clients import run_llm, run_llm_async
from core.title_classfication_v2.utils.logger import get_logger

logger = get_logger("classifier")

def classify_documents(pages: str, system_prompt: str, user_prompt: str, max_retries: int = 5) -> ClassificationResponse:
    try:
        parser = PydanticOutputParser(pydantic_object=ClassificationResponse)
        user_prompt = user_prompt.format(PAGES=pages)

        # Retry loop
        for attempt in range(max_retries):
            try:
                response_text, reasoning = run_llm(system_prompt, user_prompt)
                if not response_text:
                    raise ValueError("Empty response from LLM")

                result = parser.parse(response_text)
                result.classes.sort(key=lambda x: x.label)
                return result

            except ValidationError as e:
                logger.warning(f"[Attempt {attempt + 1}/{max_retries}] ValidationError: {e}")
                if attempt == max_retries - 1:
                    raise
            except Exception as e:
                logger.warning(f"[Attempt {attempt + 1}/{max_retries}] LLM error: {e}")
                if attempt == max_retries - 1:
                    raise

        raise ValueError("Classification failed after maximum retries")

    except Exception as e:
        logger.error(f"Document classification failed. Reason: {e}")
        return ClassificationResponse(classes=[])
    
async def classify_documents_async(pages: str, system_prompt: str, user_prompt: str, max_retries: int = 5) -> ClassificationResponse:
    try:
        parser = PydanticOutputParser(pydantic_object=ClassificationResponse)
        user_prompt = user_prompt.format(PAGES=pages)

        # Retry loop
        for attempt in range(max_retries):
            try:
                response_text, reasoning = await run_llm_async(system_prompt, user_prompt)
                if not response_text:
                    raise ValueError("Empty response from LLM")

                result = parser.parse(response_text)
                result.classes.sort(key=lambda x: x.label)
                return result

            except ValidationError as e:
                logger.warning(f"[Attempt {attempt + 1}/{max_retries}] ValidationError: {e}")
                if attempt == max_retries - 1:
                    raise
            except Exception as e:
                logger.warning(f"[Attempt {attempt + 1}/{max_retries}] LLM error: {e}")
                if attempt == max_retries - 1:
                    raise

        raise ValueError("Classification failed after maximum retries")

    except Exception as e:
        logger.error(f"Document classification failed. Reason: {e}")
        return ClassificationResponse(classes=[])