from util.config import Config


class GPTConfig(Config):
    model: str
    code_model: str
    temperature: float
    code_temperature: float
    max_tokens: int
    presence_penalty: float

    def __init__(self):
        super().__init__("ai")

    def _init_defaults(self):
        self.model = "text-davinci-003"
        self.code_model = "code-davinci-002"
        self.temperature = 0.1
        self.code_temperature = 0.1
        self.max_tokens = 512
        self.presence_penalty = 0.5
