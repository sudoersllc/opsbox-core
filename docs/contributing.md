# Contributing to Opsbox

Thank you for your interest in contributing to Opsbox! 

We welcome contributions in the form of bug reports, feature requests, documentation improvements, new rego checks, and code changes. To ensure a smooth and efficient collaboration process, please follow these guidelines.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Coding Standards](#coding-standards)
4. [Branching Strategy](#branching-strategy)
5. [Precommit Hooks](#precommit-hooks)
6. [Submitting Changes](#submitting-changes)

## Code of Conduct

By participating in the Opsbox project, you agree to abide by the following guidelines:

1. **Respectful Interaction**: Treat all participants with respect. Consider different viewpoints and experiences.
2. **Inclusivity**: Promote a diverse and inclusive environment.
3. **Effective Communication**: Use clear and constructive language. Be open to feedback and collaborate effectively.
4. **Issue Reporting**: Report any unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork to your local machine:
   ```bash
   git clone https://github.com/sudoersllc/OpsBox.git
   cd opsbox
   ```
3. Install UV for dependency management:
   ```bash
   pipx install uv
   ```
4. Install the project dependencies:
   ```bash
   uv sync
   ```
5. Install precommit hooks:
   ```bash
   uv run pre-commit install
   ```

## Coding Standards

- **Docstrings**: All classes and functions must have docstrings in Google style. This ensures consistency and helps others understand your code.
  ```python
  def example_function(param1: int, param2: str) -> bool:
      """
      Example function that demonstrates Google style docstrings.

      Args:
          param1 (int): The first parameter.
          param2 (str): The second parameter.

      Returns:
          bool: The return value. True for success, False otherwise.
      """
      return True
  ```

- **Formatting and Linting**: We use `ruff` for formatting and linting. Make sure to run `ruff` before submitting your changes.
  ```bash
  uv run ruff .
  ```

## Branching Strategy

- Create a new branch for each task you work on. This helps in managing and reviewing changes effectively.
  ```bash
  git checkout -b feature/your-feature-name
  ```

- Branch names should be descriptive and follow the convention: `feature/your-feature-name`, `bugfix/your-bugfix-name`, etc.

## Precommit Hooks

We use precommit hooks to ensure code quality and consistency. Make sure to install and use them:
```bash
uv run pre-commit install
```
These hooks will automatically run checks and formatting tools before you commit changes.

## Submitting Changes

1. Ensure your code follows the coding standards mentioned above.
2. Run all tests to make sure nothing is broken.
3. Commit your changes with a clear and concise commit message:
   ```bash
   git add .
   git commit -m "Add feature/fix for ..."
   ```
4. Push your branch to GitHub:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Open a pull request on GitHub and describe your changes in detail.

Thank you for contributing to Opsbox!