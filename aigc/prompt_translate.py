from zhipuai import ZhipuAI  # type: ignore


class ZhipuaiClient:

    def __init__(self, api_key: str) -> None:
        self._client = ZhipuAI(api_key=api_key)

    def translate(self, text: str) -> str:
        response = self._client.chat.completions.create(
            model="glm-4-air-250414", messages=[
                {"role": "user", "content": f"请将下列内容翻译成英语，如果原文已经是英语，请返回原文：{text}"}
            ]
        )
        return response.choices[0].message.content # type: ignore
