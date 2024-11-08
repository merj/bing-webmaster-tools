# Bing Webmaster Tools API Client

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

### Simple Example
Here's a basic example showing how to get site information and analyze traffic:

```python
from bing_webmaster_tools import Settings, BingWebmasterClient


async def main():
    # Initialize client with settings from environment
    async with BingWebmasterClient(Settings.from_env()) as client:
        # Get all sites
        sites = await client.sites.get_sites()
        if not sites:
            print("No sites available")
            return

        test_site = sites[0].url
        print(f"Using site: {test_site}")

        # Get traffic stats
        traffic_stats = await client.traffic.get_rank_and_traffic_stats(test_site)
        print("Traffic Statistics:")
        for stat in traffic_stats:
            print(f"Date: {stat.date}")
            print(f"Clicks: {stat.clicks}")
            print(f"Impressions: {stat.impressions}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

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

### Site Management
Handles site registration, verification, and role management:

```python
# Get all sites
sites = await client.sites.get_sites()

# Add and verify a new site
await client.sites.add_site("https://example.com")
is_verified = await client.sites.verify_site("https://example.com")

# Manage site roles
roles = await client.sites.get_site_roles("https://example.com")
```

### Content Management
Manages URL information and content analysis:

```python
# Get URL information
url_info = await client.content.get_url_info(site_url, page_url)

# Get child URLs information
children = await client.content.get_children_url_info(
    site_url,
    parent_url,
    page=0,
    filter_properties=FilterProperties(
        crawl_date_filter=CrawlDateFilter.LAST_WEEK,
        discovered_date_filter=DiscoveredDateFilter.LAST_MONTH
    )
)
```

### Traffic Analysis
Analyzes search traffic and ranking data:

```python
# Get ranking and traffic statistics
stats = await client.traffic.get_rank_and_traffic_stats(site_url)

# Get query-specific statistics
query_stats = await client.traffic.get_query_stats(site_url)
page_stats = await client.traffic.get_page_stats(site_url)
```

### Link Analysis
Manages inbound links and deep links:

```python
# Get link counts
link_counts = await client.links.get_link_counts(site_url)

# Get URL-specific links
url_links = await client.links.get_url_links(site_url, url)

# Get connected pages
connected = await client.links.get_connected_pages(site_url)
```

### Keyword Analysis
Analyzes keyword performance:

```python
# Get keyword data
keyword_data = await client.keywords.get_keyword(
    query="python programming",
    country="us",
    language="en-US",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

# Get related keywords
related = await client.keywords.get_related_keywords(
    query="python",
    country="us",
    language="en-US",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)
```

### Content Blocking
Manages URL blocking and page preview settings:

```python
# Block a URL
await client.blocking.add_blocked_url(
    site_url,
    blocked_url,
    entity_type=BlockedUrl.BlockedUrlEntityType.PAGE
)

# Manage page previews
await client.blocking.add_page_preview_block(
    site_url,
    url,
    reason=BlockReason.COPYRIGHT
)
```

### URL Management
Handles URL parameters and normalization:

```python
# Manage query parameters
params = await client.urls.get_query_parameters(site_url)
await client.urls.add_query_parameter(site_url, "sort")
await client.urls.enable_disable_query_parameter(site_url, "sort", True)
```

### Submission Service
Handles URL and content submission:

```python
# Submit URLs
await client.submission.submit_url(site_url, page_url)
await client.submission.submit_url_batch(site_url, [url1, url2])

# Manage feeds
await client.submission.submit_feed(site_url, feed_url)
quota = await client.submission.get_url_submission_quota(site_url)
```

### Crawling Service
Manages crawl settings and monitoring:

```python
# Get and update crawl settings
settings = await client.crawling.get_crawl_settings(site_url)
await client.crawling.save_crawl_settings(
    site_url,
    CrawlSetting(
        crawl_boost_available=True,
        crawl_boost_enabled=True,
        crawl_rate=[5] * 24  # 24 hourly rates
    )
)

# Get crawl statistics
stats = await client.crawling.get_crawl_stats(
    site_url,
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

# Get crawl issues
issues = await client.crawling.get_crawl_issues(site_url)
```

### Regional Settings
Manages country and region-specific settings:

```python
# Get current settings
settings = await client.regional.get_country_region_settings(site_url)

# Add new regional settings
await client.regional.add_country_region_settings(
    site_url,
    CountryRegionSettings(
        date=datetime.now(),
        two_letter_iso_country_code="US",
        type=CountryRegionSettingsType.DOMAIN,
        url="https://example.com"
    )
)

# Remove regional settings
await client.regional.remove_country_region_settings(
    site_url,
    settings  # Existing settings to remove
)
```

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
