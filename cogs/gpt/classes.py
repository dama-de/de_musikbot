from util.config import Config


class GPTConfig(Config):
    chat_model: str
    system_message: str

    def __init__(self):
        super().__init__("ai")

    def _init_defaults(self):
        self.chat_model = "gpt-5-nano"
        self.system_message = "You are a helpful assistant."
