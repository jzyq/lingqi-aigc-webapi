from zhipuai import ZhipuAI


class ZhipuaiClient:

    def __init__(self, api_key: str) -> None:
        self._client = ZhipuAI(api_key=api_key)

    def translate(self, model: str, hint: str, text: str) -> str:
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

    def heaven_album_prompt(self, model: str, hint: str, character_desc: str) -> str:
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
