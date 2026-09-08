import os
import cloudinary
import cloudinary.uploader
import cloudinary.api

CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

try:
    import config
    if hasattr(config, 'CLOUDINARY_CLOUD_NAME'):
        CLOUDINARY_CLOUD_NAME = config.CLOUDINARY_CLOUD_NAME
    if hasattr(config, 'CLOUDINARY_API_KEY'):
        CLOUDINARY_API_KEY = config.CLOUDINARY_API_KEY
    if hasattr(config, 'CLOUDINARY_API_SECRET'):
        CLOUDINARY_API_SECRET = config.CLOUDINARY_API_SECRET
except ImportError:
    pass

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True
    )

def upload_image(file, folder="swimtrackpro/general"):
    """
    Upload an image file to Cloudinary.
    Returns the secure URL of the uploaded image or None if failed.
    """
    try:
        if not file:
            return None
        response = cloudinary.uploader.upload(file, folder=folder)
        return response.get('secure_url')
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None

def delete_image(url):
    """
    Delete an image from Cloudinary using its URL.
    """
    try:
        if not url:
            return False
            
        parts = url.split('/')
        if 'upload' in parts:
            upload_idx = parts.index('upload')
            public_id_with_ext = "/".join(parts[upload_idx+2:])
            public_id = public_id_with_ext.rsplit('.', 1)[0]
            
            response = cloudinary.uploader.destroy(public_id)
            return response.get('result') == 'ok'
    except Exception as e:
        print(f"Cloudinary delete error: {e}")
    return False

def get_images_in_folder(folder="swimtrackpro/general"):
    """
    Fetch all images in a specific Cloudinary folder.
    """
    try:
        response = cloudinary.api.resources(type="upload", prefix=folder)
        return [res.get('secure_url') for res in response.get('resources', [])]
    except Exception as e:
        print(f"Cloudinary fetch error: {e}")
        return []
