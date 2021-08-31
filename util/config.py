import json
import os


class Config:

    def __init__(self, name: str):
        self._name = name
        self._data = {}

        self.datadir = os.environ["DATA_DIR"] if "DATA_DIR" in os.environ else "./data/"
        self.datafile = os.path.join(self.datadir, f"{name}.json")

        self.load()
        self.save()

    @property
    def data(self):
        return self._data

    def save(self):
        with open(self.datafile, "w") as file:
            file.write(json.dumps(self.data))
            file.close()

    def load(self):
        if os.path.exists(self.datafile):
            with open(self.datafile, "r") as file:
                data = json.loads(file.read())
