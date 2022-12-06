import json
import logging
import os
from pathlib import Path
from typing import Any, get_type_hints

_log = logging.getLogger(__name__)


class Config:
    """Helper class for reading and writing json-based config files. The data for one file is shared across
    all :class:`Config` instances pointing to that file. You may create subclasses in the following style:

    .. code-block:: python3

        class MyConfig(Config):
            my_str: str
            my_int: int

            def __init__(self):
                super().__init__(self, "myconfig")

            def _init_defaults(self):
                self.my_int = 5
    """
    __slots__ = ["_name", "_data", "datadir", "datafile"]
    _instances = {}

    def __init__(self, name: str):
        self._name = name
        self._data = {}

        self.datadir = os.environ["DATA_DIR"] if "DATA_DIR" in os.environ else "./data/"
        self.datafile = os.path.join(self.datadir, f"{name}.json")

        # If this file is already known, just make our self._data point to the existing data
        if name in Config._instances:
            self._data = Config._instances[name]
        else:
            Config._instances[name] = self.data
            Path(self.datadir).mkdir(parents=True, exist_ok=True)
            self._init_defaults()
            self.load()

    def _init_defaults(self):
        """Subclasses should set their default values in here instead of `__init__`"""
        pass

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Config):
            return self.name == o.name and self.data is o.data
        else:
            return False

    def __getattr__(self, name: str) -> Any:
        # This only gets called if the attribute could not be found by other means
        # As this is a config, in that case we try to get the attribute from our datastore
        if name in self.data:
            # Check if there is a type hint for optimistic casting
            hints = get_type_hints(self.__class__)
            if name in hints:
                hinted_type = hints[name]
                return hinted_type(self.data[name])
            else:
                return self.data[name]

    def __setattr__(self, name: str, value: Any) -> None:
        # Prefer __slots__ over config data
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            # Check if there is a type hint for optimistic casting
            hints = get_type_hints(self.__class__)
            if name in hints:
                hinted_type = hints[name]
                self.data[name] = hinted_type(value)
            else:
                self.data[name] = value
            self.save()

    @property
    def name(self) -> str:
        return self._name

    @property
    def data(self) -> dict:
        return self._data

    def save(self):
        with open(self.datafile, "w") as file:
            file.write(json.dumps(self.data))
            file.close()

    def load(self) -> bool:
        if os.path.exists(self.datafile):
            with open(self.datafile, "r") as file:
                self.data.update(json.loads(file.read()))
                return True
        return False
