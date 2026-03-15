from importlib import import_module


def test_package_imports() -> None:
    module = import_module("asd_shop")
    assert module is not None
