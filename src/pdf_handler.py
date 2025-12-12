"""
PDF Handler Module - Convert PDF pages to images for OCR.
Uses PyMuPDF (fitz) as primary method - no external dependencies required.
Falls back to pdf2image if available.
"""
import os
from typing import List, Optional
from PIL import Image
import io

# Try to import PyMuPDF (fitz) - preferred, no external dependencies
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# Try to import pdf2image as fallback (requires Poppler)
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


def check_pdf_support() -> bool:
    """Check if PDF support is available."""
    return PYMUPDF_AVAILABLE or PDF2IMAGE_AVAILABLE


def get_pdf_backend() -> str:
    """Get the name of the PDF backend being used."""
    if PYMUPDF_AVAILABLE:
        return "PyMuPDF"
    elif PDF2IMAGE_AVAILABLE:
        return "pdf2image (Poppler)"
    return "None"


def pdf_to_images(pdf_path: str, dpi: int = 200, 
                  first_page: Optional[int] = None,
                  last_page: Optional[int] = None) -> List[Image.Image]:
    """
    Convert PDF pages to PIL Images.
    
    Args:
        pdf_path: Path to PDF file.
        dpi: Resolution for conversion (higher = better quality but slower).
        first_page: First page to convert (1-indexed). None for start.
        last_page: Last page to convert (1-indexed). None for end.
        
    Returns:
        List of PIL Image objects, one per page.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF soubor nenalezen: {pdf_path}")
    
    # Use PyMuPDF if available (preferred - no external dependencies)
    if PYMUPDF_AVAILABLE:
        return _pdf_to_images_pymupdf(pdf_path, dpi, first_page, last_page)
    
    # Fall back to pdf2image (requires Poppler)
    if PDF2IMAGE_AVAILABLE:
        return _pdf_to_images_pdf2image(pdf_path, dpi, first_page, last_page)
    
    raise ImportError(
        "Žádná PDF knihovna není dostupná.\n"
        "Nainstalujte PyMuPDF: pip install PyMuPDF"
    )


def _pdf_to_images_pymupdf(pdf_path: str, dpi: int = 200,
                           first_page: Optional[int] = None,
                           last_page: Optional[int] = None) -> List[Image.Image]:
    """Convert PDF to images using PyMuPDF."""
    images = []
    
    # Open PDF
    doc = fitz.open(pdf_path)
    
    try:
        # Calculate page range (convert from 1-indexed to 0-indexed)
        start_idx = (first_page - 1) if first_page else 0
        end_idx = last_page if last_page else len(doc)
        
        # Clamp to valid range
        start_idx = max(0, start_idx)
        end_idx = min(len(doc), end_idx)
        
        # Calculate zoom factor for DPI (default PDF is 72 DPI)
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        
        for page_num in range(start_idx, end_idx):
            page = doc[page_num]
            
            # Render page to pixmap
            pixmap = page.get_pixmap(matrix=matrix)
            
            # Convert to PIL Image
            img_data = pixmap.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            # Convert to RGB if necessary (some PDFs have alpha channel)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            images.append(image)
    
    finally:
        doc.close()
    
    return images


def _pdf_to_images_pdf2image(pdf_path: str, dpi: int = 200,
                             first_page: Optional[int] = None,
                             last_page: Optional[int] = None) -> List[Image.Image]:
    """Convert PDF to images using pdf2image (requires Poppler)."""
    kwargs = {'dpi': dpi}
    if first_page is not None:
        kwargs['first_page'] = first_page
    if last_page is not None:
        kwargs['last_page'] = last_page
    
    try:
        images = convert_from_path(pdf_path, **kwargs)
        return images
    except Exception as e:
        if "poppler" in str(e).lower():
            raise ImportError(
                "pdf2image vyžaduje Poppler.\n"
                "Stáhněte z: https://github.com/osber/poppler/releases\n"
                "Nebo nainstalujte PyMuPDF: pip install PyMuPDF"
            ) from e
        raise


def get_page_count(pdf_path: str) -> int:
    """
    Get number of pages in PDF.
    
    Args:
        pdf_path: Path to PDF file.
        
    Returns:
        Number of pages.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF soubor nenalezen: {pdf_path}")
    
    if PYMUPDF_AVAILABLE:
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    
    if PDF2IMAGE_AVAILABLE:
        from pdf2image.pdf2image import pdfinfo_from_path
        info = pdfinfo_from_path(pdf_path)
        return info.get('Pages', 0)
    
    raise ImportError("Žádná PDF knihovna není dostupná.")


def pdf_page_to_image(pdf_path: str, page_number: int, dpi: int = 200) -> Image.Image:
    """
    Convert a specific PDF page to PIL Image.
    
    Args:
        pdf_path: Path to PDF file.
        page_number: Page number (1-indexed).
        dpi: Resolution for conversion.
        
    Returns:
        PIL Image of the specified page.
    """
    images = pdf_to_images(pdf_path, dpi=dpi, first_page=page_number, last_page=page_number)
    if images:
        return images[0]
    raise ValueError(f"Stránka {page_number} nebyla nalezena.")


def is_pdf_file(file_path: str) -> bool:
    """
    Check if file is a PDF based on extension.
    
    Args:
        file_path: Path to file.
        
    Returns:
        True if file has .pdf extension.
    """
    return file_path.lower().endswith('.pdf')


def is_image_file(file_path: str) -> bool:
    """
    Check if file is a supported image format.
    
    Args:
        file_path: Path to file.
        
    Returns:
        True if file is a supported image format.
    """
    supported = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp')
    return file_path.lower().endswith(supported)


def get_supported_formats() -> List[str]:
    """
    Get list of supported file formats.
    
    Returns:
        List of supported file extensions.
    """
    formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp']
    if check_pdf_support():
        formats.append('.pdf')
    return formats
