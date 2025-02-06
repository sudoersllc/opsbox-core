import pytest

from opsbox.plugins import Registry
from pydantic import ValidationError
from tomllib import TOMLDecodeError

# ruff: noqa: S101 

def test_toml_load_success(test_registry: Registry):
    """Test the loading of a TOML file."""
    registry = test_registry
    item = registry.read_toml_spec("tests/test_plugins/rego_plugin/manifest.toml")

    assert item.name == "test_plugin_2"
    assert item.module == "test_2"
    assert item.class_name == "Test2"
    assert item.type == "rego_test"

    description = "Check for inactive S3 objects."
    rego_file = "test_2.rego"

    assert item.extra["rego"]["description"] == description
    assert item.extra["rego"]["rego_file"] == rego_file

def test_toml_spec_validation_err(test_registry: Registry):
    """Test the loading of a TOML file."""
    registry = test_registry
    with pytest.raises((ValidationError, KeyError)):
        registry.read_toml_spec("tests/invalid_test_plugins/invalid_key/manifest.toml")

def test_toml_spec_decode_err(test_registry: Registry):
    """Test the loading of a TOML file."""
    registry = test_registry
    with pytest.raises(TOMLDecodeError):
        registry.read_toml_spec("tests/invalid_test_plugins/invalid_toml/manifest.toml")
