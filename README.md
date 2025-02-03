# Opsbox

**AI-Powered Infrastructure Management**

Welcome to Opsbox, the open-source platform that adds a dash of AI magic to your infrastructure management. With our flexible plugin system and policy-as-code approach using Rego, managing your infrastructure has never been this enjoyable!

## Features

- 🎛️ **Plugin System**: Customize and extend functionality with ease.
- 📝 **Policy-as-Code with Rego**: Define compliance checks and policies efficiently.
- 🤖 **AI Assistance**: Leverage AI models to analyze and process your infrastructure data.
- 💻 **Command-Line Interface**: An interactive CLI.
- 📚 **Documentation Support**: Generate and view documentation effortlessly using mkdocs.

# Installation

## Prerequisites

Ensure you have [Python 3.11](https://www.python.org/downloads/) installed.

For an isolated installation, use either [UV](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io/stable/).

For **development** or [installing from source](#install-from-source), you'll need [UV](https://docs.astral.sh/uv/).

For **Rego plugins**, [install OPA](#installing-opa-for-rego-compatibility).

---

## (Recommended) Install in an Isolated Environment

Installing in an isolated environment avoids system conflicts and pollution.

### Using UV

#### Installation
```bash
uv tool install opsbox
```
To install with extras:
```bash
uv tool install --with "opsbox-cli-output" "opsbox[aws]"
```
To add packages after installation:
```bash
uv tool install --with "existing-packages new-package"
```
> **Warning:** If UV downloads the wrong version or can't find a package, clear the cache:
> ```bash
> uv cache clean
> ```

#### Execution
```bash
uv tool run opsbox ...
```
Or:
```bash
uvx opsbox ...
```
> **Warning:** Do not use `--with` during execution; it creates a temporary environment.

### Using pipx

#### Installation
```bash
pipx install opsbox
```
To install additional packages:
```bash
pipx inject opsbox opsbox-cli-output
```
To ensure `opsbox` is in your PATH:
```bash
pipx ensurepath
```
Run `opsbox` directly in your shell.

---

## (Not Recommended) Install from Source

For development or debugging, install from source using UV.

### Installation
```bash
git clone https://github.com/sudoersllc/opsbox-core.git
cd opsbox-core
uv sync
```
> **Note:** If you encounter Python versioning issues:
> ```bash
> uv python install 3.11
> rm .python-version
> uv python pin 3.11
> ```

### Execution
Run `opsbox/main.py` inside the virtual environment:
```bash
uv run ./opsbox/main.py ...
```

---

## Installing OPA for Rego Compatibility

If using Rego (e.g., AWS plugins), install [OPA](https://www.openpolicyagent.org/docs/latest/#running-opa) and add it to your system `PATH`.

### Adding OPA to PATH

#### Linux/macOS
```bash
echo 'export PATH=$PATH:/path/to/opa' >> ~/.bashrc
source ~/.bashrc  # or source ~/.zshrc
```
#### Windows
1. Open "Edit the system environment variables" > "Environment Variables...".
2. Edit "Path" and add `C:\path\to\opa\directory`.
3. Restart your terminal.

> **Note:** To use an existing OPA server, pass its URL in `opa_url`.

---

### Example Usage

Want to run a specific pipeline? Here's how:

```bash
uv run opsbox --modules your_input-your_optional_assistant-your_output
```

A recommended command to start is stray_ebs make sure you have opsbox[aws] and opsbox-cli-output installed

```bash
uv run opsbox --modules stray_ebs-cli_out --aws_access_key_id {YOUR_ACCESS_KEY_ID} --aws_secret_access_key {YOUR_SECRET_ACCESS_KEY} --aws_region us-east-1
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
}
```

To run a command with a config it will follow this format
```bash
uv run opsbox --modules stray_ebs-cli_out --config config.json
```

### Command-Line Arguments

You can also provide configuration options directly through the command line:

```bash
uvx opsbox --modules example_module --aws_access_key_id YOUR_ACCESS_KEY_ID --aws_secret_access_key YOUR_SECRET_ACCESS_KEY --aws_region YOUR_AWS_REGION
```

## Plugins
You'll probably want some plugins to get started!

Opsbox plugins published by gsudoers normally take the format of `opsbox-<name>-<plugin_type>`, and are accessible and searchable through PyPI.

There's also a collection of plugins available for AWS systems, installable by using the pip extras group `aws`:

```pip install 'opsbox[aws]'```


## Let's Get Started!

Now that you're all set, it's time to unleash the power of AI on your infrastructure. Happy automating!
