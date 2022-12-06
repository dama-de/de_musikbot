import traceback

import discord
import openai
from discord import Interaction
from discord.ext.commands import Cog, Bot, Context, hybrid_command, is_owner, command

from cogs.gpt.classes import GPTConfig
from util.config import Config


# TODO - Messages over 2000 chars


async def setup(bot: Bot):
    await bot.add_cog(GPT())


class GPT(Cog):
    def __init__(self) -> None:
        self._config = GPTConfig()

    @hybrid_command()
    @is_owner()
    async def gpt_model(self, ctx: Context):
        await ctx.reply(view=SettingsView(self._config), ephemeral=True)

    @command()
    @is_owner()
    async def gpt_temp(self, ctx: Context, temperature: float):
        self._config.temperature = temperature
        self._config.save()
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @hybrid_command()
    async def gpt(self, ctx: Context, query: str):
        if ctx.interaction is None:
            query = ctx.message.clean_content[len(ctx.clean_prefix) + len(ctx.invoked_with) + 1:]
        async with ctx.typing():
            try:
                completion = openai.Completion.create(
                    model=self._config.model,
                    prompt=query,
                    user=ctx.author.name,
                    temperature=self._config.temperature,
                    max_tokens=self._config.max_tokens
                )
                await ctx.reply(completion.choices[0].text)
            except openai.error.InvalidRequestError as e:
                await ctx.reply("".join(traceback.format_exception_only(type(e), e)))


class SettingsView(discord.ui.View):
    def __init__(self, config: Config):
        super().__init__()
        self.add_item(ModelDropdown(config))


class ModelDropdown(discord.ui.Select):
    def __init__(self, config: Config):
        self._config = config

        models = ["text-davinci-003", "text-curie-001", "code-davinci-002", "code-cushman-001"]
        selected_model = self._config.model

        options = [
            discord.SelectOption(label=model, value=model, default=(model == selected_model))
            for model in models
        ]

        super().__init__(placeholder="Choose a model", options=options)

    async def callback(self, interaction: Interaction):
        self._config.model = self.values[0]
        self._config.save()
        await interaction.response.send_message("Ok", delete_after=1, ephemeral=True)
