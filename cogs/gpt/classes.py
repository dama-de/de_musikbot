from util.config import Config


class GPTConfig(Config):
    chat_model: str
    system_message: str
    temperature: float
    presence_penalty: float

    def __init__(self):
        super().__init__("ai")

    def _init_defaults(self):
        self.chat_model = "gpt-3.5-turbo"
        self.system_message = "You are a helpful assistant."
        self.temperature = 0.1
        self.presence_penalty = 0.5
