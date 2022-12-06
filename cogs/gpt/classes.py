from util.config import Config


class GPTConfig(Config):
    model: str
    temperature: float
    max_tokens: int

    def __init__(self):
        super().__init__("ai")

    def _init_defaults(self):
        self.model = "text-davinci-003"
        self.temperature = 0.1
        self.max_tokens = 512
