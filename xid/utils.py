"""File operations and content saving utilities."""

from pathlib import Path
from typing import Optional, List


def save_tweet_content_v2(
    tweet,
    folder_path: Path,
    username: str,
    image_urls: Optional[List[str]] = None
) -> None:
    """Save tweet text content to a .txt file (API v2 format).
    
    Args:
        tweet: Tweet object from API v2
        folder_path: Directory to save the tweet content
        username: Twitter username of the tweet author
        image_urls: Optional list of image URLs associated with the tweet
    """
    txt_path = folder_path / "tweet.txt"
    
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"Tweet ID: {tweet.id}\n")
        f.write(f"Created at: {tweet.created_at}\n")
        f.write(f"Author: @{username}\n")
        f.write(f"Text:\n{tweet.text}\n")
        
        if image_urls:
            f.write(f"\nImage URLs:\n")
            for idx, url in enumerate(image_urls, 1):
                f.write(f"  {idx}. {url}\n")


def create_tweet_folder(output_path: Path, tweet_created_at) -> Path:
    """Create a folder for tweet content.
    
    Args:
        output_path: Base output directory
        tweet_created_at: Datetime when the tweet was created
        
    Returns:
        Path to the created folder
    """
    folder_name = tweet_created_at.strftime("%Y%m%d_%H%M%S")
    tweet_folder = output_path / folder_name
    tweet_folder.mkdir(exist_ok=True)
    return tweet_folder
