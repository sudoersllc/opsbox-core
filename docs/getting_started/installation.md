# Installing

You have three options for installing the project:

- **From PyPI**: Install the program using releases from PyPI
- **Manual Install**: Install the program locally using Python and UV.
- **Docker Container**: Install the program using a Docker dev container, which includes OPA for policy enforcement.

## From PyPI
We provide pip-installable packages for your convenience.

To install, simply run the following in your desired virtual environment:
```pip install opsbox```

If using uv, you can add it:
```uv add opsbox```

Note that this version of setup does not include OPA, and that has to be downloaded and run seperately to use rego-based plugins.

If you don't have an OPA server set up yet, follow the instructions in the [Using Rego Plugins](#using-rego-plugins) section.

## Manual Installation
### Prerequisites

Ensure you have the following installed on your machine:

- [Python](https://www.python.org/downloads/) == 3.11
- [UV](https://docs.astral.sh/uv/) for dependency management

**Installing Python:**

Visit the [official Python website](https://www.python.org/downloads/) and download the latest version of Python for your operating system.

**Installing UV**

UV can be installed in various ways. The recommended method is to use the installer script:


*For Linux/Mac*

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

*For Windows*
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Clone the Project from GitHub

First, clone the repository to get a local copy of the project:

[OpsBox GitHub Repository](https://github.com/sudoersllc/OpsBox.git)

### Install Dependencies

Navigate to the project directory. Use UV to sync the project dependencies:

```bash
uv sync
```

### Using Rego Plugins
Open Policy Agent (OPA) is an open-source policy engine that enables organizations to implement policy as code across diverse environments. Its policy language, Rego, allows users to define rules that dictate system and application behavior.

We use rego code to gather details about connected systems, alongside an Open Policy Agent (OPA) server, then format it for consumption by a language model.

#### Create a OPA Policy docker image
To run OpsBox with rego plugins, you'll need an OPA server. This is because OpsBox uses OPA to enforce policies on all resources that are being managed.

if you don't have OPA installed on your machine, or you dont have a running OPA instance, you can create a docker image for OPA.

Create a dockerfile and add the following code:
```docker
    # Use the official OPA image
    FROM openpolicyagent/opa:latest

    # Expose OPA's default port
    EXPOSE 8181

    # Run OPA with the specified policy file
    CMD ["run", "--server", "--addr", "0.0.0.0:8181"]
```

Navigate to the directory and Build the Docker image:
```bash
    docker build -t name_of_file .
```
or you can also follow the offical OPA documentation to create the engine: [OPA Documentation](https://www.openpolicyagent.org/docs/latest/)

## Using supplied `docker-compose.yml`
This project supports development inside a Docker container for consistent environments across different machines.

While our docker images are stored in the `.devcontainer` folder, they can be used to build consistent environments.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) >= 20.10.7 for containers

### Building the Docker Image

The provided `Dockerfile` and `docker-compose.yml` files facilitate building a Docker image with all necessary dependencies, including Python, UV, and setting up OPA for rego plugins.

To build and start the container, run:

```bash
docker-compose up --build
```

This command builds the Docker image for the application and starts an OPA service in another container *(default port is 8181)*. The `docker-compose.yml` file is configured to mount the project directory inside the container for live code updates.

Now, you can execute commands to the composed service through using traditional docker compose commands.


### Setting Up OPA

The `docker-compose.yml` file automatically sets up an OPA instance running in server mode. It exposes port 8181 for accessing the OPA API. You can interact with OPA using its REST API or by accessing the OPA service directly from within the application container.
