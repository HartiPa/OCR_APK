"""
OCR Engine Module - Tesseract wrapper for text extraction.
"""
import os
import pytesseract
from PIL import Image
from typing import Optional, List, Dict, Any


class OCREngine:
    """Wrapper for Tesseract OCR engine."""
    
    def __init__(self, tesseract_path: Optional[str] = None, language: str = "ces+eng"):
        """
        Initialize OCR Engine.
        
        Args:
            tesseract_path: Path to tesseract executable. If None, uses system PATH.
            language: OCR language(s). Default is Czech + English.
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.language = language
        self._verify_tesseract()
    
    def _verify_tesseract(self) -> None:
        """Verify Tesseract is available."""
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            raise RuntimeError(
                "Tesseract OCR není nainstalován nebo není v PATH.\n"
                "Stáhněte z: https://github.com/UB-Mannheim/tesseract/wiki"
            ) from e
    
    def get_available_languages(self) -> List[str]:
        """Get list of available OCR languages."""
        try:
            return pytesseract.get_languages()
        except Exception:
            return []
    
    def extract_text(self, image_path: str) -> str:
        """
        Extract all text from an image.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Extracted text as string.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Soubor nenalezen: {image_path}")
        
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=self.language)
        return text.strip()
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extract text from PIL Image object.
        
        Args:
            image: PIL Image object.
            
        Returns:
            Extracted text as string.
        """
        text = pytesseract.image_to_string(image, lang=self.language)
        return text.strip()
    
    def extract_text_with_positions(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Extract text with bounding box positions.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            List of dictionaries with text and position data.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Soubor nenalezen: {image_path}")
        
        image = Image.open(image_path)
        data = pytesseract.image_to_data(image, lang=self.language, output_type=pytesseract.Output.DICT)
        
        results = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text:
                results.append({
                    'text': text,
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'confidence': data['conf'][i]
                })
        
        return results
    
    def extract_text_with_confidence(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text with overall confidence score.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Dictionary with text and average confidence.
        """
        positions = self.extract_text_with_positions(image_path)
        
        if not positions:
            return {'text': '', 'confidence': 0}
        
        full_text = ' '.join([p['text'] for p in positions])
        confidences = [p['confidence'] for p in positions if p['confidence'] > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'text': full_text,
            'confidence': avg_confidence
        }
