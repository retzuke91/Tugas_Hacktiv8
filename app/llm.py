import json
import logging
from typing import Any, Generator
from google import genai
from google.genai import types
from app.config import settings
from app.tools import TOOLS_REGISTRY, TOOL_DECLARATIONS

log = logging.getLogger(__name__)

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY tidak dikonfigurasi.")
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def run_chat(
    history: list[dict[str, Any]],
    new_message: str,
    system_prompt: str,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
) -> str:
    """Run one turn of chat with function calling loop. Returns final text reply."""
    client = get_client()
    temp = temperature if temperature is not None else settings.DEFAULT_TEMPERATURE
    max_tok = max_output_tokens if max_output_tokens is not None else settings.DEFAULT_MAX_OUTPUT_TOKENS

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=TOOL_DECLARATIONS,
        temperature=temp,
        max_output_tokens=max_tok,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    # Build history for SDK
    sdk_history: list[types.Content] = []
    for msg in history:
        role = msg["role"]
        if role == "tool":
            continue  # tool results are handled inline
        content = msg["content"]
        sdk_history.append(types.Content(
            role="user" if role == "user" else "model",
            parts=[types.Part.from_text(text=content)]
        ))

    chat = client.chats.create(model=settings.GEMINI_MODEL, config=config, history=sdk_history)

    response = chat.send_message(new_message)

    # Function calling loop
    MAX_ROUNDS = 5
    for _ in range(MAX_ROUNDS):
        if not response.function_calls:
            break

        tool_results: list[types.Part] = []
        for fc in response.function_calls:
            fn = TOOLS_REGISTRY.get(fc.name)
            if fn is None:
                result = {"error": f"Tool '{fc.name}' tidak ditemukan."}
            else:
                try:
                    args = dict(fc.args) if fc.args else {}
                    result = fn(**args)
                    log.info("Tool %s called with %s → %s", fc.name, args, result)
                except Exception as e:
                    log.error("Tool %s error: %s", fc.name, e)
                    result = {"error": str(e)}

            tool_results.append(
                types.Part.from_function_response(
                    name=fc.name,
                    response=result if isinstance(result, dict) else {"result": result}
                )
            )

        response = chat.send_message(tool_results)

    text = response.text or ""
    return text.strip()


def run_chat_stream(
    history: list[dict[str, Any]],
    new_message: str,
    system_prompt: str,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
) -> Generator[str, None, None]:
    """Streaming variant — yields text chunks. Falls back to full response on tool calls."""
    # Resolve function calling first, then stream final text
    final_text = run_chat(history, new_message, system_prompt, temperature, max_output_tokens)
    # Yield word by word to simulate streaming feel
    words = final_text.split(" ")
    for i, word in enumerate(words):
        yield word if i == len(words) - 1 else word + " "
