import pytest


# ruff: noqa: S101
def test_set_attribute(app_config):
    """Test setting an attribute."""
    config = app_config
    config["test"] = "test"
    assert config["test"] == "test"


def test_delete_attribute(app_config):
    """Test deleting an attribute."""
    config = app_config
    config["test"] = "test"
    del config["test"]
    # assert keyerror
    with pytest.raises(AttributeError):
        config["test"]


def test_set_attribute_to_none(app_config):
    """Test setting an attribute to None."""
    config = app_config
    config["test"] = None
    assert config["test"] is None


def test_delete_non_existent_attribute(app_config):
    """Test deleting a non-existent attribute."""
    config = app_config
    with pytest.raises(AttributeError):  # Assuming KeyError is the correct exception
        del config["non_existent"]


def test_set_multiple_attributes(app_config):
    """Test setting multiple attributes."""
    config = app_config
    config["attr1"] = "value1"
    config["attr2"] = 123
    config["attr3"] = [1, 2, 3]
    assert config["attr1"] == "value1"
    assert config["attr2"] == 123
    assert config["attr3"] == [1, 2, 3]
