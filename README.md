# x-image-downloader - Twitter/X Image Downloader

A Python CLI tool to download tweets with images from X (formerly Twitter) using the Twitter API.

## Features

- Fetch tweets from any public Twitter/X account
- Filter and download only tweets that contain images
- Download original quality images
- Organize downloads in folders named by tweet datetime (YYYYMMDD_HHMMSS)
- Save tweet content (text, likes, retweets) in a .txt file alongside images
- Automatically exclude retweets

## Installation

1. Install dependencies using Poetry:
```bash
poetry install
```

2. Set up your Twitter API credentials:
   - Create a Twitter Developer account at https://developer.twitter.com/
   - Create a new app and get your API credentials
   - Copy `.env.example` to `.env`
   - Fill in your credentials in the `.env` file

```bash
cp .env.example .env
# Edit .env with your credentials
```

## Usage

```bash
# Download tweets from a user (saves to 'downloads' folder by default)
poetry run xid <username>

# Specify a custom output directory
poetry run xid <username> <output_directory>

# Only fetch tweets since a specific date (yyyy-mm-dd format)
poetry run xid <username> <output_directory> <start_date>
```

### Examples

```bash
# Download images from @elonmusk's tweets
poetry run xid elonmusk

# Save to a custom folder
poetry run xid nasa nasa_images

# Download tweets only since a specific date
poetry run xid nasa nasa_images 2025-01-15
```

## Output Structure

The tool creates a folder for each tweet with images:

```
downloads/
├── 20231215_143022/
│   ├── image_1.jpg
│   ├── image_2.jpg
│   └── tweet.txt
├── 20231214_091530/
│   ├── image_1.jpg
│   └── tweet.txt
└── ...
```

Each `tweet.txt` file contains:
- Tweet ID
- Creation date/time
- Author username
- Full tweet text
- Like count
- Retweet count

## Requirements

- Python >= 3.13
- Twitter API credentials (API Key, API Secret, Access Token, Access Token Secret)

## API Rate Limits

Twitter's API has rate limits. The tool will automatically wait when rate limits are hit. For the standard free tier:
- User timeline: 900 requests per 15-minute window
- Each request can fetch up to 200 tweets

## License

MIT
