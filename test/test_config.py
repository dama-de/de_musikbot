from util.config import Config


# Tests for util.config.Config

def test_config_instances():
    a = Config("_foo")
    b = Config("_foo")
    c = Config("_bar")

    # Should be equal, but not the same object
    assert a == b
    assert a is not b

    # Should point to the same data
    assert a._data is b._data

    # Should be inequal to different configs
    assert a != c


def test_config_subclassing():
    class SubConfig(Config):
        my_string: str
        my_int: int
        my_float: float
        my_default: str

        def __init__(self):
            super().__init__("_test")

        def _init_defaults(self):
            self.my_default = "test"

    # Initialize, write some data to it and reload from disk
    conf = SubConfig()
    conf.my_string = "hello world"
    conf.my_int = 5
    conf.my_float = 0.3
    conf.load()

    assert conf.my_int == 5
    assert conf.my_float == 0.3
    # Test that properties are written through to the actual data
    assert conf.my_string == conf.data["my_string"] == "hello world"
    assert conf.my_int == conf.data["my_int"] == 5
    assert conf.my_float == conf.data["my_float"] == 0.3
    assert conf.my_default == conf.data["my_default"] == "test"


def test_new_instance_does_not_overwrite_existing_file():
    # TODO Implement
    pass


def test_default_values_are_discarded_on_fetch_from_cache():
    class DefaultedConfig(Config):
        my_default: str

        def _init_defaults(self):
            self.my_default = "default"

    conf = DefaultedConfig("_default")
    assert conf.my_default == "default"

    conf.my_default = "foobar"

    conf2 = DefaultedConfig("_default")
    assert conf._data is conf2._data
    assert conf2.my_default == "foobar"


def test_casting():
    class CastingConfig(Config):
        my_int: int

    conf = CastingConfig("_cast1")
    conf2 = CastingConfig("_cast2")

    conf.my_int = "5"
    conf2.my_int = "0"
    assert conf.my_int == 5
    assert conf2.my_int == 0


def test_load_subclass_from_superclass_constructor():
    class LoadFromSuperclassConfig(Config):
        my_int: int

        def __init__(self):
            super().__init__("_load_from_superclass")

    conf = LoadFromSuperclassConfig()
    conf.my_int = 5

    conf2 = Config("_load_from_superclass")
    assert conf2.data["my_int"] == 5
