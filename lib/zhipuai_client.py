from zhipuai import ZhipuAI
import asyncio


class ZhipuaiClient:

    def __init__(self, api_key: str) -> None:
        self._client = ZhipuAI(api_key=api_key)

    async def translate(self, model: str, hint: str, text: str) -> str:
        return await asyncio.to_thread(self.__translate_blocking_io, model, hint, text)

    def __translate_blocking_io(self, model: str, hint: str, text: str) -> str:
        response = self._client.chat.completions.create(
            model="glm-4-air-250414",
            messages=[
                {
                    "role": "user",
                    "content": f"请将下列内容翻译成英语，如果原文已经是英语，请返回原文：{text}",
                }
            ],
        )
        return response.choices[0].message.content  # type: ignore

    async def heaven_album_prompt(
        self, model: str, hint: str, character_desc: str
    ) -> str:
        return await asyncio.to_thread(
            self.__heaven_album_prompt_blocking_io, model, hint, character_desc
        )

    def __heaven_album_prompt_blocking_io(
        self, model: str, hint: str, character_desc: str
    ) -> str:
        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": hint,
                },
                {
                    "role": "user",
                    "content": character_desc,
                },
            ],
        )
        return response.choices[0].message.content  # type: ignore
