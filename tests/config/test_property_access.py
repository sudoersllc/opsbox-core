import pytest


# ruff: noqa: S101
def test_set_attribute(appconfig):
    """Test setting an attribute."""
    config = appconfig
    config["test"] = "test"
    assert config["test"] == "test"


def test_delete_attribute(appconfig):
    """Test deleting an attribute."""
    config = appconfig
    config["test"] = "test"
    del config["test"]
    # assert keyerror
    with pytest.raises(AttributeError):
        config["test"]


def test_set_attribute_to_none(appconfig):
    """Test setting an attribute to None."""
    config = appconfig
    config["test"] = None
    assert config["test"] is None


def test_delete_non_existent_attribute(appconfig):
    """Test deleting a non-existent attribute."""
    config = appconfig
    with pytest.raises(AttributeError):  # Assuming KeyError is the correct exception
        del config["non_existent"]


def test_set_multiple_attributes(appconfig):
    """Test setting multiple attributes."""
    config = appconfig
    config["attr1"] = "value1"
    config["attr2"] = 123
    config["attr3"] = [1, 2, 3]
    assert config["attr1"] == "value1"
    assert config["attr2"] == 123
    assert config["attr3"] == [1, 2, 3]
