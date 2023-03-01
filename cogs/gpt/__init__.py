import re

import discord
from discord import Interaction
from discord.ext.commands import Cog, Bot, Context, hybrid_command, is_owner

import util
from cogs.gpt.ai import AIError
from cogs.gpt.classes import GPTConfig


async def setup(bot: Bot):
    await bot.add_cog(GPT())


class GPT(Cog):
    def __init__(self) -> None:
        self._config = GPTConfig()

    @hybrid_command(hidden=True)
    @is_owner()
    async def gpt_model(self, ctx: Context):
        """Choose the GPT models used"""
        await ctx.reply(content="Choose the models", view=SettingsView(self._config), ephemeral=True)

    @hybrid_command()
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

    @hybrid_command()
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
                text = f"```{text}\n```"
                await util.split_message(text, ctx)
            except AIError as e:
                await ctx.reply(str(e))

    @hybrid_command()
    async def chatgpt(self, ctx: Context, *, prompt: str):
        """Talk to ChatGPT!"""
        async with ctx.typing():
            try:
                text = await ai.chat_completion(prompt, self._config.system_message, model=self._config.chat_model,
                                                temperature=self._config.code_temperature,
                                                presence_penalty=self._config.presence_penalty,
                                                user=ctx.author.name)
                text = f"> {prompt}\n\n{text}"
                await util.split_message(text, ctx)
            except AIError as e:
                await ctx.reply(str(e))


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
