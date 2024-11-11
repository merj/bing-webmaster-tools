# Bing Webmaster Tools API Client

[![PyPI version](https://img.shields.io/pypi/v/bing-webmaster-tools.svg)](https://pypi.org/project/bing-webmaster-tools/)
[![Python versions](https://img.shields.io/pypi/pyversions/bing-webmaster-tools.svg)](https://pypi.org/project/bing-webmaster-tools/)
[![License](https://img.shields.io/pypi/l/bing-webmaster-tools.svg)](https://github.com/merj/bing-webmaster-tools/blob/main/LICENSE)
[![CI](https://github.com/merj/bing-webmaster-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/merj/bing-webmaster-tools/actions/workflows/ci.yml)


An async Python client library for the [Bing Webmaster Tools API](https://learn.microsoft.com/en-us/bingwebmaster/), providing a clean interface for managing websites, analyzing search traffic, handling content submissions, and more.

## Overview

### Description
The Bing Webmaster API Client is a modern, async Python library that provides a comprehensive interface to Bing Webmaster Tools API. The library is designed with a focus on developer experience, type safety, and reliability, offering structured access to all Bing Webmaster Tools features through a clean, domain-driven API.

### Key Features
- **Async/await support** - Built on aiohttp for efficient async operations
- **Type-safe** - Full typing support with runtime validation using Pydantic
- **Domain-driven design** - Operations organized into logical service groups
- **Comprehensive** - Complete coverage of Bing Webmaster Tools API
- **Developer-friendly** - Intuitive interface with detailed documentation
- **Reliable** - Built-in retry logic, rate limiting, and error handling
- **Flexible** - Support for both Pydantic models and dictionaries as input
- **Production-ready** - Extensive logging, testing, and error handling

### Requirements
- Python 3.9 or higher
- Bing Webmaster API key (follow the instructions [here](https://learn.microsoft.com/en-us/bingwebmaster/getting-access#using-api-key))

## Installation

### PyPI Installation
Install the package using pip:
```bash
pip install bing-webmaster-tools
```

## Quick Start

### Basic Setup
1. Get your API key from [Bing Webmaster Tools](https://www.bing.com/webmasters)

2. Set your API key as an environment variable:
```bash
export BING_WEBMASTER_API_KEY=your_api_key_here
```

Or use a .env file:
```env
BING_WEBMASTER_API_KEY=your_api_key_here
```

## Examples

Look under the [examples](./examples) subdirectory to see boilerplate scripts which can help you get started. These assume you are using the environment variable `BING_WEBMASTER_API_KEY` as described in the [Basic Setup](#basic-setup).

### Authentication
The client supports several ways to provide authentication:

1. Environment variables (recommended):
```python
client = BingWebmasterClient(Settings.from_env())
```

2. Direct initialization:
```python
client = BingWebmasterClient(Settings(api_key="your_api_key_here"))
```

3. Configuration file:
```python
from dotenv import load_dotenv
load_dotenv()  # Load from .env file
client = BingWebmasterClient(Settings.from_env())
```

## Usage

### Client Initialization
The client can be initialized in several ways:

```python
from bing_webmaster_tools import Settings, BingWebmasterClient

# Using environment variables
async with BingWebmasterClient(Settings.from_env()) as client:
    sites = await client.sites.get_sites()

# Direct initialization
settings = Settings(
    api_key="your_api_key",
    timeout=30,  # Custom timeout
    max_retries=5  # Custom retry count
)
async with BingWebmasterClient(settings) as client:
    sites = await client.sites.get_sites()

# Manual session management
client = BingWebmasterClient(Settings.from_env())
await client.init()
try:
    sites = await client.sites.get_sites()
finally:
    await client.close()
```

### Configuration Options
The client behavior can be customized through the Settings class:

```python
from bing_webmaster_tools import Settings

settings = Settings(
    # Required
    api_key="your_api_key",  # Also via BING_WEBMASTER_API_KEY env var

    # Optional with defaults
    base_url="https://ssl.bing.com/webmaster/api.svc/json",
    timeout=30,  # Request timeout in seconds
    max_retries=3,  # Maximum number of retry attempts
    rate_limit_calls=10,  # Number of calls allowed per period
    rate_limit_period=1,  # Rate limit period in seconds
    disable_destructive_operations=False
    # Disable destructive operations, if you want to prevent accidental deletions etc. 
)
```

Environment variables can be used with the `BING_WEBMASTER_` prefix:
```bash
BING_WEBMASTER_API_KEY=your_api_key
BING_WEBMASTER_TIMEOUT=60
BING_WEBMASTER_MAX_RETRIES=5
```

### Error Handling
The client provides structured error handling:

```python
from bing_webmaster_tools.exceptions import (
    BingWebmasterError,
    AuthenticationError,
    RateLimitError
)


async def handle_api_calls():
    try:
        await client.sites.get_sites()
    except AuthenticationError:
        # Handle authentication issues
        print("Check your API key")
    except RateLimitError:
        # Handle rate limiting
        print("Too many requests")
    except BingWebmasterError as e:
        # Handle other API errors
        print(f"API error: {e.message}, Status: {e.status_code}")
```

### Rate Limiting
The client includes built-in rate limiting:
- Default: 5 calls per second
- Configurable via settings
- Automatic retry with exponential backoff on rate limit errors

To turn off rate limiting, simply set the rate limit configuration variables to `None`.

## Services

The client provides access to different API functionalities through specialized services.
For full details on available services and methods, refer to the [API documentation](https://learn.microsoft.com/en-us/dotnet/api/microsoft.bing.webmaster.api.interfaces?view=bing-webmaster-dotnet).


## Development

### Development Installation
To install from source for development:

```bash
# Clone the repository
git clone https://github.com/merj/bing-webmaster-tools
cd bing-webmaster-tools

# Install poetry if you haven't already
pip install poetry

# Install dependencies and setup development environment
poetry install
```
