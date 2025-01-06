from unittest.mock import patch

from core.config import find_config_file

# ruff: noqa: S101


# region find_config
@patch("core.config.path.isfile", return_value=True)
@patch("core.config.path.expanduser", return_value="/mock/home")
def test_find_config_file_found(mock_expanduser, mock_isfile):
    """Test config. file finding."""
    filename = ".opsbox_conf.json"
    config_path = find_config_file(filename)
    assert (config_path == "/mock/home/.opsbox_conf.json") | (config_path == "/mock/home\\.opsbox_conf.json")
    mock_isfile.assert_called_once_with(config_path)


@patch("core.config.path.isfile", return_value=False)
@patch("core.config.path.expanduser", return_value="/mock/home")
def test_find_config_file_not_found(mock_expanduser, mock_isfile):
    """Test config. file not found."""
    filename = ".opsbox_conf.json"
    config_path = find_config_file(filename)
    assert config_path is None


# endregion find_config
