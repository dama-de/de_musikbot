import asyncio

import openai


async def completion(prompt, *, model: str = "text-davinci-003", **kwargs):
    try:
        completion = await asyncio.to_thread(openai.Completion.create, prompt=prompt, model=model, **kwargs)
        return completion.choices[0].text
    except openai.error.OpenAIError as e:
        raise AIError(str(e))


class AIError(Exception):
    pass
