import os
import sys

import openai
from dotenv import load_dotenv

sys.path.append("configs")
from config import ChatGPTConfig


class PromptConverter:
    def __init__(self, chatgpt_config: ChatGPTConfig):
        self.config = chatgpt_config
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def convert(self, sentence: str) -> str:
        system_setting = {"role": "system", "content": self.config.system_prompt}
        user_input = {"role": "user", "content": sentence}
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=[system_setting, user_input]
        )
        response = response.choices[0].message.content
        return response


if __name__ == "__main__":
    from omegaconf import OmegaConf

    example_1 = "Make it a character-like image of a cute anime"
    print("入力文")
    print(example_1)
    chatgpt_config = OmegaConf.create(ChatGPTConfig)
    prompt_converter = PromptConverter(chatgpt_config)
    prompt = prompt_converter.convert(example_1)
    print("プロンプト")
    print(prompt)
