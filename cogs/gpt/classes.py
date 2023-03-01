from util.config import Config


class GPTConfig(Config):
    model: str
    chat_model: str
    code_model: str
    system_message: str
    temperature: float
    code_temperature: float
    max_tokens: int
    presence_penalty: float

    def __init__(self):
        super().__init__("ai")

    def _init_defaults(self):
        self.model = "text-davinci-003"
        self.chat_model = "gpt-3.5-turbo"
        self.code_model = "code-davinci-002"
        self.system_message = "You are a helpful assistant."
        self.temperature = 0.1
        self.code_temperature = 0.1
        self.max_tokens = 512
        self.presence_penalty = 0.5
