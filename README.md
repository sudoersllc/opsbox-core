# Opsbox

**AI-Powered Infrastructure Management**

Welcome to Opsbox, the open-source platform that adds a dash of AI magic to your infrastructure management. With our flexible plugin system and policy-as-code approach using Rego, managing your infrastructure has never been this enjoyable!

## Features

- 🎛️ **Plugin System**: Customize and extend functionality with ease.
- 📝 **Policy-as-Code with Rego**: Define compliance checks and policies efficiently.
- 🤖 **AI Assistance**: Leverage AI models to analyze and process your infrastructure data.
- 💻 **Command-Line Interface**: An interactive CLI.
- 📚 **Documentation Support**: Generate and view documentation effortlessly using mkdocs.

## Installation

Ready to dive in? Let's get you set up!

### Prerequisites

- **Python 3.11**
- **uv**

### Through PyPI

Simply run `pip install opsbox` to install the minimal set of opsbox tools.

If using UV, run `uv add opsbox`

*Note: If you want to install AWS plugins, use the aws extras group, `opsbox[aws]`*

### Through Github

1. **Clone the Repository**

    ```bash
    git clone https://github.com/sudoersllc/Opsbox.git
    cd Opsbox
    ```

2. **Install with uv**

    We use [`uv`] for managing dependencies. If you don't have it installed, you can get it via pip:

    ```bash
    pip install uv
    ```

    Now, let's install Opsbox:

    ```bash
    uv sync
    ```

    This command will install all required dependencies specified in `pyproject.toml`.

## Running Opsbox

Time to see the magic in action!

Simply run:

```bash
uv run opsbox ...
```

or, if not using UV:

```bash
python -m opsbox ...
```

This will launch Opsbox and display the CLI help along with available commands.

### Example Usage

Want to run a specific pipeline? Here's how:

```bash
uv run opsbox --modules your_input-your_optional_assistant-your_output --opa_upload_url http://your-opa-upload-url --opa_apply_url http://your-opa-apply-url
```

or, if not using UV:

```bash
python -m opsbox --modules your_input-your_optional_assistant-your_output --opa_upload_url http://your-opa-upload-url --opa_apply_url http://your-opa-apply-url
```

## Configuration

Opsbox is flexible when it comes to configuration. You can provide options via:

- **Command-Line Arguments**
- **Configuration Files**
- **Environment Variables**

### Using a Configuration File

Create a file named `.opsbox_conf.json` in your home directory:

```json
{
  "aws_access_key_id": "YOUR_ACCESS_KEY_ID",
  "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY",
  "aws_region": "YOUR_AWS_REGION",
  "opa_upload_url": "http://your-opa-upload-url",
  "opa_apply_url": "http://your-opa-apply-url"
}
```

### Command-Line Arguments

You can also provide configuration options directly through the command line:

```bash
python -m opsbox --modules example_module --aws_access_key_id YOUR_ACCESS_KEY_ID --aws_secret_access_key YOUR_SECRET_ACCESS_KEY --aws_region YOUR_AWS_REGION --opa_upload_url http://your-opa-upload-url --opa_apply_url http://your-opa-apply-url
```

## Plugins
You'll probably want some plugins to get started!

Opsbox plugins published by gsudoers normally take the format of `opsbox-<name>-<plugin_type>`, and are accessible and searchable through PyPI.

There's also a collection of plugins available for AWS systems, installable by using the pip extras group `aws`:

```pip install 'opsbox[aws]'```


## Let's Get Started!

Now that you're all set, it's time to unleash the power of AI on your infrastructure. Happy automating!