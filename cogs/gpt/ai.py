import asyncio

import openai


async def completion(prompt, *, model: str = "text-davinci-003", **kwargs):
    try:
        completion = await asyncio.to_thread(openai.Completion.create, prompt=prompt, model=model, **kwargs)
        return completion.choices[0].text
    except openai.error.OpenAIError as e:
        raise AIError(str(e))


async def history_completion(history, *, model: str = "gpt-3.5-turbo", **kwargs):
    try:
        completion = openai.ChatCompletion.create(
            model=model,
            messages=history,
            **kwargs
        )
        return completion.choices[0].message.content
    except openai.error.OpenAIError as e:
        raise AIError(str(e))


async def chat_completion(prompt, system_message, *, model: str = "gpt-3.5-turbo", **kwargs):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]

    return await history_completion(messages, model=model, **kwargs)


class AIError(Exception):
    pass
