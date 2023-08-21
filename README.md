# Semantic Kernel Auto Document Generator

A command line tool that uses Microsoft's Semantic Kernel and LLMs to generate code documentation.

## Prerequisites

- [Python](https://www.python.org/downloads/) 3.8 and above
  - [Poetry](https://python-poetry.org/) is used for packaging and dependency management
  - [Semantic Kernel Tools](https://marketplace.visualstudio.com/items?itemName=ms-semantic-kernel.semantic-kernel)

## Configure

This can be configured with a `.env` file in the project which holds api keys and other secrets and configurations.

Make sure you have an
[Open AI API Key](https://openai.com/api/) or
[Azure Open AI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)

Copy the `.env.example` file to a new file named `.env`. Then, copy those keys into the `.env` file:

```
OPENAI_API_KEY=""
OPENAI_ORG_ID=""
AZURE_OPENAI_DEPLOYMENT_NAME=""
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_API_KEY=""
```

## Running

To run:

```powershell
poetry install
poetry run sk-autodocs --help
```

To rewrite code in your directory:

```powershell
poetry install
poetry run sk-autodocs --path .
```

To rewrite dotnet code from a build log that contains CS1591 warnings:

```powershell
poetry install
poetry run sk-autodocs --dotnet-build-log path/to/build.log
```
