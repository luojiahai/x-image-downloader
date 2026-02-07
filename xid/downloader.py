"""Image downloading utilities."""

import requests
from pathlib import Path


def download_image(image_url: str, save_path: Path) -> bool:
    """Download an image from URL to the specified path.
    
    Args:
        image_url: URL of the image to download
        save_path: Path where the image should be saved
        
    Returns:
        True if download was successful, False otherwise
    """
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


def extract_filename_from_url(url: str) -> str:
    """Extract filename from URL, handling Twitter size suffixes.
    
    Args:
        url: Image URL
        
    Returns:
        Cleaned filename
    """
    # Remove query parameters
    url_path = url.split('?')[0]
    # Get last part of path
    image_filename = url_path.split('/')[-1]
    
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
    
    return image_filename
