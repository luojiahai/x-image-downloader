import os
import sys
import tweepy
import requests
from pathlib import Path
from dotenv import load_dotenv


def download_image(image_url, save_path):
    """Download an image from URL to the specified path."""
    # Get original quality image by removing size modifiers
    original_url = image_url.split('?')[0]  # Remove query parameters
    
    # Remove Twitter size suffix like :large, :medium, :small (only at the end)
    size_suffixes = [':large', ':medium', ':small', ':thumb']
    for suffix in size_suffixes:
        if original_url.endswith(suffix):
            original_url = original_url[:-len(suffix)]
            break
    
    try:
        response = requests.get(original_url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading image:")
        print(f"  Original URL: {image_url}")
        print(f"  Modified URL: {original_url}")
        print(f"  Error: {e}")
        return False


def save_tweet_content(tweet, folder_path):
    """Save tweet text content to a .txt file (API v1.1 format)."""
    txt_path = folder_path / "tweet.txt"
    
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"Tweet ID: {tweet.id}\n")
        f.write(f"Created at: {tweet.created_at}\n")
        f.write(f"Author: @{tweet.user.screen_name}\n")
        f.write(f"Text:\n{tweet.text}\n")
        
        if hasattr(tweet, 'favorite_count'):
            f.write(f"\nLikes: {tweet.favorite_count}\n")
        if hasattr(tweet, 'retweet_count'):
            f.write(f"Retweets: {tweet.retweet_count}\n")


def save_tweet_content_v2(tweet, folder_path, username, image_urls=None):
    """Save tweet text content to a .txt file (API v2 format)."""
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


def get_tweets_with_images(username, output_dir="downloads", start_date=None):
    """Fetch tweets from a user and download images.
    
    Args:
        username: Twitter username to fetch tweets from
        output_dir: Directory to save downloaded content
        start_date: Optional date in yyyy-mm-dd format to only fetch tweets since this date
    """
    # Load environment variables
    load_dotenv()
    
    # Get API credentials from environment variables
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    
    if not bearer_token:
        print("Error: Missing Twitter API credentials in environment variables.")
        print("Please set TWITTER_BEARER_TOKEN in your .env file")
        print("You can get a Bearer Token from: https://developer.twitter.com/en/portal/dashboard")
        return
    
    # Authenticate with Twitter API v2
    client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)
    
    print(f"Authentication successful! Fetching tweets from @{username}...")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Fetch tweets (excluding retweets)
    tweets_processed = 0
    tweets_with_images = 0
    
    try:
        # Get user ID from username
        user = client.get_user(username=username)
        if not user.data:
            print(f"Error: User @{username} not found")
            return
        
        user_id = user.data.id
        
        # Get user's tweets with media fields
        # API v2 uses pagination with max_results per page
        pagination_token = None
        max_tweets = 200
        
        while tweets_processed < max_tweets:
            # Prepare request parameters
            request_params = {
                'id': user_id,
                'max_results': 100,  # Max per request in API v2
                'exclude': ['retweets', 'replies'],
                'tweet_fields': ['created_at', 'attachments'],
                'media_fields': ['type', 'url', 'width', 'height'],
                'expansions': ['attachments.media_keys'],
                'pagination_token': pagination_token
            }
            
            # Add start_time filter if date was provided
            if start_date:
                # Convert yyyy-mm-dd to ISO 8601 format (yyyy-mm-ddT00:00:00Z)
                request_params['start_time'] = f"{start_date}T00:00:00Z"
            
            response = client.get_users_tweets(**request_params)
            
            if not response.data:
                break
            
            # Create a media lookup dictionary
            media_dict = {}
            if response.includes and 'media' in response.includes:
                for media in response.includes['media']:
                    media_dict[media.media_key] = media
            
            # Process each tweet
            for tweet in response.data:
                tweets_processed += 1
                
                # Check if tweet has media attachments
                if hasattr(tweet, 'attachments') and tweet.attachments:
                    media_keys = tweet.attachments.get('media_keys', [])
                    
                    # Filter only photos
                    photos = [media_dict[key] for key in media_keys 
                             if key in media_dict and media_dict[key].type == 'photo']
                    
                    if photos:
                        tweets_with_images += 1
                        
                        # Create folder name from tweet datetime
                        folder_name = tweet.created_at.strftime("%Y%m%d_%H%M%S")
                        tweet_folder = output_path / folder_name
                        tweet_folder.mkdir(exist_ok=True)
                        
                        print(f"\nProcessing tweet from {tweet.created_at}...")
                        print(f"  Found {len(photos)} image(s)")
                        
                        # Collect image URLs
                        image_urls = []
                        
                        # Download all images
                        for idx, photo in enumerate(photos, 1):
                            # Get the image URL from the media object
                            if hasattr(photo, 'url') and photo.url:
                                image_url = photo.url
                            else:
                                print(f"  Warning: No URL found for image {idx}, skipping...")
                                continue
                            
                            image_urls.append(image_url)
                            
                            # Extract original filename from URL
                            url_path = image_url.split('?')[0]  # Remove query parameters
                            image_filename = url_path.split('/')[-1]  # Get last part of path
                            
                            # Handle URLs with size suffixes
                            size_suffixes = [':large', ':medium', ':small', ':thumb']
                            for suffix in size_suffixes:
                                if image_filename.endswith(suffix):
                                    # Split off the suffix and get the extension
                                    name_part = image_filename[:-len(suffix)]
                                    # Re-add extension if it was removed
                                    if '.' in name_part:
                                        image_filename = name_part
                                    break
                            
                            image_path = tweet_folder / image_filename
                            
                            print(f"  Downloading image {idx}/{len(photos)}...")
                            if not download_image(image_url, image_path):
                                print(f"  Failed to download image. Stopping.")
                                return
                            print(f"    Saved: {image_path}")
                        
                        # Save tweet content (v2 format)
                        save_tweet_content_v2(tweet, tweet_folder, username, image_urls)
                        print(f"  Saved tweet content to {tweet_folder / 'tweet.txt'}")
            
            # Check if there are more pages
            if response.meta and 'next_token' in response.meta and tweets_processed < max_tweets:
                pagination_token = response.meta['next_token']
            else:
                break
        
        print(f"\n✓ Done! Processed {tweets_processed} tweets")
        print(f"  Found {tweets_with_images} tweets with images")
        print(f"  Files saved to: {output_path.absolute()}")
        
    except tweepy.TweepyException as e:
        print(f"Error fetching tweets: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def main():
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

