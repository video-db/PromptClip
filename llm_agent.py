"""
Extend this codebase to add any LLM
"""
import json
import os

import requests
from openai import OpenAI
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class LLMType:
    OPENAI = "openAI"
    CLAUDE = "claude"
    GEMINI = "gemini"


class Models:
    GPT4o = "gpt-4o"
    GPT4o_mini = "gpt-4o-mini"
    GPTo3 = "o3"
    GPTo3_mini = "o3-mini"

    CLAUDE4_SONNET = "claude-sonnet-4-20250514"

    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_PRO = "gemini-2.5-pro"


class LLM:
    def __init__(self, llm_type=LLMType.OPENAI, model=Models.GPT4o):

        self.type = llm_type
        self.model = model
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.claude_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")

    def chat(self, message, temperature=0.6, functions=None):

        if self.type == LLMType.OPENAI:
            message = [self._to_gpt_msg(message)]
            return self._call_openai(message, temperature, functions)
        elif self.type == LLMType.CLAUDE:
            return self._call_claude(message, temperature)
        elif self.type == LLMType.GEMINI:
            return self._call_gemini(message, temperature)
        else:
            raise ValueError("Unsupported LLM type.")

    def _to_gpt_msg(self, data):
        """
        convert data to message for LLM
        :param data:
        :return:
        """
        context_msg = ""
        context_msg += str(data)

        return {"role": "user", "content": context_msg}

    def _call_openai(self, message, temperature=0.6, functions=None):

        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
        client = OpenAI(api_key=self.openai_key)

        # Build the base payload
        payload = {
            "model": self.model,
            "messages": message,
            "response_format": {"type": "json_object"},
        }

        if "o3" not in self.model:
            payload.update({"temperature": temperature})

        if functions:
            payload.update({
                "tools": functions,
                "tool_choice": "auto",
            })

        try:
            response = client.chat.completions.create(**payload)
            content = response.choices[0].message.content
            return json.loads(content)
        except json.JSONDecodeError:
            return {"error": "Failed to decode JSON response."}
        except Exception as e:
            return {"error": str(e)}

    def _call_claude(self, message, temperature=0.6):

        anthropic = Anthropic(api_key=self.claude_key)
        prompt = f"{HUMAN_PROMPT} {message} {AI_PROMPT}"
        try:
            completion = anthropic.completions.create(
                model=self.model,
                max_tokens_to_sample=80000,
                prompt=prompt,
                temperature=temperature,
            )
            return {"response": completion.completion}
        except (
            Exception
        ) as e:
            print(f'call claude with error: {e}')
            return {"error": str(e)}

    def _call_gemini(self, message, temperature=0.6):

        if not self.gemini_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")

        # Google provides an OpenAI-compatible endpoint for Gemini models (currently in beta)
        client = OpenAI(
            api_key=self.gemini_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

        # Ensure the message is wrapped in the expected list-of-dicts format
        if isinstance(message, str):
            messages = [self._to_gpt_msg(message)]
        else:
            messages = message  # assume already formatted

        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": temperature,
        }

        try:
            response = client.chat.completions.create(**payload)
            content = response.choices[0].message.content

            return json.loads(content)
        except json.JSONDecodeError:
            return {"error": "Failed to decode JSON response."}
        except Exception as e:
            return {"error": str(e)}
