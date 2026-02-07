"""Command-line interface for x-image-downloader."""

import sys
from .twitter import get_tweets_with_images


def main() -> None:
    """Main entry point for the CLI."""
    if len(sys.argv) < 2:
        print("Usage: xid <username> [output_directory] [start_date]")
        print("\nExample: xid elonmusk")
        print("         xid elonmusk my_downloads")
        print("         xid elonmusk my_downloads 2025-01-15")
        sys.exit(1)
    
    username = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "downloads"
    start_date = sys.argv[3] if len(sys.argv) > 3 else None
    
    get_tweets_with_images(username, output_dir, start_date)
