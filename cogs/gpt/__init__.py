import logging
import re
from typing import List

import discord
from discord import Interaction, Message
from discord.ext.commands import Cog, Bot, Context, hybrid_command, is_owner

import util
from cogs.gpt.ai import AIError
from cogs.gpt.classes import GPTConfig

_log = logging.getLogger(__name__)


async def setup(bot: Bot):
    await bot.add_cog(GPT(bot))


class GPT(Cog):
    def __init__(self, bot: Bot) -> None:
        self._config = GPTConfig()
        self._bot = bot

    @hybrid_command(hidden=True, enabled=False)
    @is_owner()
    async def gpt_model(self, ctx: Context):
        """Choose the GPT models used"""
        await ctx.reply(content="Choose the models", view=SettingsView(self._config), ephemeral=True)

    @hybrid_command(enabled=False)
    async def gpt(self, ctx: Context, *, prompt: str):
        """Let a GPT-3 AI respond to your prompt. Try \"Tell me a joke!\""""
        async with ctx.typing():
            try:
                text = await ai.completion(prompt, model=self._config.model, temperature=self._config.temperature,
                                           max_tokens=self._config.max_tokens,
                                           presence_penalty=self._config.presence_penalty,
                                           user=ctx.author.name)
                text = f"> {prompt}{text}"
                await util.split_message(text, ctx)
            except AIError as e:
                await ctx.reply(str(e))

    @hybrid_command(enabled=False)
    async def code(self, ctx: Context, *, prompt: str):
        """Let a GPT-3 AI complete your code. Format your prompt like a comment, and mention the language."""
        async with ctx.typing():
            try:
                text = await ai.completion(prompt, model=self._config.code_model,
                                           temperature=self._config.code_temperature,
                                           max_tokens=self._config.max_tokens,
                                           presence_penalty=self._config.presence_penalty,
                                           echo=True,
                                           user=ctx.author.name)
                # Remove the line-prefix
                text = re.sub(r"^\+", "", text, flags=re.MULTILINE)
                await util.split_message(text, ctx, prefix="```\n", suffix="\n```")
            except AIError as e:
                await ctx.reply(str(e))

    @hybrid_command()
    async def chatgpt(self, ctx: Context, *, prompt: str, preprompt=""):
        """Talk to ChatGPT!"""
        if not preprompt:
            preprompt = self._config.system_message

        async with ctx.typing():
            try:
                text = await ai.chat_completion(prompt, preprompt, model=self._config.chat_model,
                                                temperature=self._config.code_temperature,
                                                presence_penalty=self._config.presence_penalty,
                                                user=ctx.author.name)
                text = f"> {prompt}\n\n{text}"
                await util.split_message(text, ctx)
            except AIError as e:
                await ctx.reply(str(e))

    @Cog.listener()
    async def on_message(self, message: Message):
        """Allow users to reply to a ChatGPT command to continue the conversation.
        This method filters for valid messages, retrieves the conversation history and creates a reply."""

        # If this is not a reply or the replied to message cannot be found, ignore
        if not message.reference or not isinstance(message.reference.resolved, Message):
            return

        # If the replied to message is not ours, ignore
        if message.reference.resolved.author.id is not self._bot.user.id:
            return

        # If the replied to message is not part of a GPT conversation, ignore
        # Walk up the conversation and see if it starts with a GPT command or interaction
        history = await self.get_reply_history(message)
        initial = history[0]

        # Check that the reply history originates in a valid conversational gpt command
        valid_cmds = ["chatgpt"]
        initial_ctx = await self._bot.get_context(initial)
        if initial.author.id is self._bot.user.id and initial.interaction and initial.interaction.name in valid_cmds:
            pass
        elif initial_ctx.valid and initial_ctx.command.name in valid_cmds:
            pass
        else:
            return

        api_history = [
            {
                "role": "assistant" if msg.author.bot else "user",
                "content": msg.clean_content
            }
            for msg in history
        ]
        api_history.insert(0, {"role": "system", "content": self._config.system_message})

        ctx = await self._bot.get_context(message)
        async with ctx.typing():
            try:
                reply = await ai.history_completion(api_history, model=self._config.chat_model,
                                                    temperature=self._config.code_temperature,
                                                    presence_penalty=self._config.presence_penalty,
                                                    user=message.author.name)

                await util.split_message(reply, ctx)
            except AIError as e:
                await ctx.reply(str(e))

    async def get_reply_history(self, message: Message) -> List[Message]:
        history = [message]
        while message.reference:
            if not message.reference.resolved:
                message.reference.resolved = await message.channel.fetch_message(message.reference.message_id)

            history.insert(0, message.reference.resolved)
            message = message.reference.resolved
        return history


class SettingsView(discord.ui.View):
    def __init__(self, config: GPTConfig):
        super().__init__()
        self.add_item(ModelDropdown(config, "model"))
        self.add_item(ModelDropdown(config, "code_model"))


class ModelDropdown(discord.ui.Select):
    def __init__(self, config: GPTConfig, key: str):
        self._config = config
        self._key = key

        models = ["text-davinci-003", "text-curie-001", "code-davinci-002", "code-cushman-001"]
        selected_model = self._config.data[key]

        options = [
            discord.SelectOption(label=f"{key}: {model}", value=model, default=(model == selected_model))
            for model in models
        ]

        super().__init__(placeholder=f"Choose a {key}", options=options)

    async def callback(self, interaction: Interaction):
        self._config.data[self._key] = self.values[0]
        self._config.save()
        # Edit the original interaction message and recreate the view to reflect saved settings
        await interaction.response.edit_message(content=f"Saved {self._key}.", view=SettingsView(self._config))
