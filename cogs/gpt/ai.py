import openai


async def history_completion(history, *, model: str = "gpt-5-nano", **kwargs):
    try:
        completion = openai.chat.completions.create(
            model=model,
            messages=history,
            **kwargs
        )
        return completion.choices[0].message.content
    except openai.OpenAIError as e:
        raise AIError(str(e))


async def chat_completion(prompt, system_message, *, model: str = "gpt-5-nano", **kwargs):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]

    return await history_completion(messages, model=model, **kwargs)


class AIError(Exception):
    pass
