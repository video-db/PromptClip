import json
import os
from dotenv import load_dotenv
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import requests

load_dotenv()
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
CLAUDE_KEY = os.getenv('ANTHROPIC_KEY')

class LLMType:
    OPENAI = 'openAI'
    CLAUDE = 'claude'

class Models:
    GPT3 = 'gpt-3.5-turbo-16k'
    GPT4 = 'gpt-4'
    CLAUDE_INSTANT = 'claude-instant-1.1'
    CLAUDE2 = 'claude-2'

class LLM:
    def __init__(self, llm_type=LLMType.OPENAI, model=Models.GPT3):
        self.type = llm_type
        self.model = model
        self.openai_key = os.getenv('OPENAI_KEY')
        self.claude_key = os.getenv('ANTHROPIC_KEY')

    def chat(self, message, functions=None):
        if self.type == LLMType.OPENAI:
            message = [self._to_gpt_msg(message)]
            return self._call_openai(message, functions)
        elif self.type == LLMType.CLAUDE:
            return self._call_claude(message)
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

        return {
            "role": 'system',
            "content": context_msg
        }

    def _call_openai(self, message, functions=None):
        url = 'https://api.openai.com/v1/chat/completions'
        # print(f'call openAI with message {message}')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.openai_key}'
        }
        data = {
            "model": self.model,
            "messages": message,
            "temperature": 0.6
        }
        if functions:
            data.update({
                "functions": functions,
                "function_call": 'auto',
            })

        response = requests.post(url, headers=headers, data=json.dumps(data))
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"error": "Failed to decode JSON response."}

    def _call_claude(self, message):
        anthropic = Anthropic(api_key=self.claude_key)
        prompt = f"{HUMAN_PROMPT} {message} {AI_PROMPT}"
        try:
            completion = anthropic.completions.create(
                model=self.model,
                max_tokens_to_sample=80000,
                prompt=prompt,
            )
            return {"response": completion.completion}
        except Exception as e:  # Consider a more specific exception based on the Anthropic SDK
            return {"error": str(e)}

    def get_word_limit(self):
        if self.type == LLMType.CLAUDE:
            return 10000
        return 2000

