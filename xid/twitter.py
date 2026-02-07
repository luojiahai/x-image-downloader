"""Twitter API operations."""

import os
import tweepy
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from .downloader import download_image, extract_filename_from_url
from .utils import save_tweet_content_v2, create_tweet_folder


def get_bearer_token() -> Optional[str]:
    """Get Twitter Bearer Token from environment variables.
    
    Returns:
        Bearer token if found, None otherwise
    """
    load_dotenv()
    return os.getenv('TWITTER_BEARER_TOKEN')


def validate_credentials() -> bool:
    """Validate that Twitter API credentials are available.
    
    Returns:
        True if credentials are valid, False otherwise
    """
    bearer_token = get_bearer_token()
    
    if not bearer_token:
        print("Error: Missing Twitter API credentials in environment variables.")
        print("Please set TWITTER_BEARER_TOKEN in your .env file")
        print("You can get a Bearer Token from: https://developer.twitter.com/en/portal/dashboard")
        return False
    
    return True


def get_tweets_with_images(
    username: str,
    output_dir: str = "downloads",
    start_date: Optional[str] = None
) -> None:
    """Fetch tweets from a user and download images.
    
    Args:
        username: Twitter username to fetch tweets from
        output_dir: Directory to save downloaded content
        start_date: Optional date in yyyy-mm-dd format to only fetch tweets since this date
    """
    # Validate credentials
    if not validate_credentials():
        return
    
    # Authenticate with Twitter API v2
    bearer_token = get_bearer_token()
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
                        
                        # Create folder for this tweet
                        tweet_folder = create_tweet_folder(output_path, tweet.created_at)
                        
                        print(f"\nProcessing tweet from {tweet.created_at}...")
                        print(f"  Found {len(photos)} image(s)")
                        
                        # Collect image URLs
                        image_urls = []
                        
                        # Download all images
                        for idx, photo in enumerate(photos, 1):
                            # Get the image URL from the media object
                            if not hasattr(photo, 'url') or not photo.url:
                                print(f"  Warning: No URL found for image {idx}, skipping...")
                                continue
                            
                            image_url = photo.url
                            image_urls.append(image_url)
                            
                            # Extract and clean filename
                            image_filename = extract_filename_from_url(image_url)
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
