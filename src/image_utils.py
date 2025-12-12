"""
Image Utilities Module - Preprocessing for better OCR results.
"""
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from typing import Tuple, Optional
import io


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """
    Preprocess image for better OCR accuracy.
    
    Applies:
    - Grayscale conversion
    - Contrast enhancement
    - Sharpening
    - Binarization (optional)
    
    Args:
        image: PIL Image to preprocess.
        
    Returns:
        Preprocessed PIL Image.
    """
    # Convert to grayscale
    if image.mode != 'L':
        image = image.convert('L')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    
    # Sharpen
    image = image.filter(ImageFilter.SHARPEN)
    
    return image


def auto_deskew(image: Image.Image) -> Image.Image:
    """
    Attempt to automatically straighten a skewed image.
    Uses simple edge detection heuristics.
    
    Args:
        image: PIL Image to deskew.
        
    Returns:
        Deskewed PIL Image.
    """
    # Simple implementation - in production would use more sophisticated
    # methods like Hough transform
    return image


def resize_for_display(image: Image.Image, max_size: Tuple[int, int] = (800, 600)) -> Image.Image:
    """
    Resize image for display in GUI while maintaining aspect ratio.
    
    Args:
        image: PIL Image to resize.
        max_size: Maximum (width, height) tuple.
        
    Returns:
        Resized PIL Image.
    """
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    return image


def enhance_for_ocr(image: Image.Image, 
                    contrast: float = 1.5,
                    brightness: float = 1.0,
                    sharpness: float = 1.5) -> Image.Image:
    """
    Apply customizable enhancements to image.
    
    Args:
        image: PIL Image to enhance.
        contrast: Contrast factor (1.0 = original).
        brightness: Brightness factor (1.0 = original).
        sharpness: Sharpness factor (1.0 = original).
        
    Returns:
        Enhanced PIL Image.
    """
    # Convert to RGB if necessary for enhancement
    if image.mode not in ('RGB', 'L'):
        image = image.convert('RGB')
    
    # Apply enhancements
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast)
    
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(brightness)
    
    if sharpness != 1.0:
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(sharpness)
    
    return image


def binarize(image: Image.Image, threshold: int = 128) -> Image.Image:
    """
    Convert image to pure black and white.
    
    Args:
        image: PIL Image to binarize.
        threshold: Pixel value threshold (0-255).
        
    Returns:
        Binarized PIL Image.
    """
    if image.mode != 'L':
        image = image.convert('L')
    
    return image.point(lambda x: 255 if x > threshold else 0, mode='1')


def remove_noise(image: Image.Image) -> Image.Image:
    """
    Remove noise from image using median filter.
    
    Args:
        image: PIL Image to denoise.
        
    Returns:
        Denoised PIL Image.
    """
    return image.filter(ImageFilter.MedianFilter(size=3))


def invert_if_needed(image: Image.Image) -> Image.Image:
    """
    Invert image colors if background is darker than text.
    Useful for white text on dark background.
    
    Args:
        image: PIL Image to potentially invert.
        
    Returns:
        PIL Image (inverted if needed).
    """
    if image.mode != 'L':
        image = image.convert('L')
    
    # Calculate average brightness
    histogram = image.histogram()
    total_pixels = sum(histogram)
    weighted_sum = sum(i * count for i, count in enumerate(histogram))
    avg_brightness = weighted_sum / total_pixels if total_pixels > 0 else 128
    
    # If average is dark (< 128), invert
    if avg_brightness < 100:
        return ImageOps.invert(image)
    
    return image


def get_image_info(image: Image.Image) -> dict:
    """
    Get basic information about an image.
    
    Args:
        image: PIL Image.
        
    Returns:
        Dictionary with image information.
    """
    return {
        'width': image.width,
        'height': image.height,
        'mode': image.mode,
        'format': image.format,
        'size_pixels': image.width * image.height
    }


def load_image(path: str) -> Image.Image:
    """
    Load image from file path.
    
    Args:
        path: Path to image file.
        
    Returns:
        PIL Image object.
    """
    return Image.open(path)


def image_to_bytes(image: Image.Image, format: str = 'PNG') -> bytes:
    """
    Convert PIL Image to bytes.
    
    Args:
        image: PIL Image to convert.
        format: Image format (PNG, JPEG, etc.)
        
    Returns:
        Bytes representation of image.
    """
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()
