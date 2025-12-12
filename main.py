#!/usr/bin/env python3
"""
OCR Desktop Application
Převod naskenovaných dokumentů na digitální text nebo strukturovaná data.

Autor: OCR App Team
Verze: 1.0.0
"""
import sys
import os

# Ensure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_dependencies():
    """Check if all required dependencies are installed."""
    missing = []
    
    try:
        import customtkinter
    except ImportError:
        missing.append("customtkinter")
    
    try:
        import pytesseract
    except ImportError:
        missing.append("pytesseract")
    
    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")
    
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    
    try:
        import openpyxl
    except ImportError:
        missing.append("openpyxl")
    
    try:
        import docx
    except ImportError:
        missing.append("python-docx")
    
    try:
        import reportlab
    except ImportError:
        missing.append("reportlab")
    
    if missing:
        print("=" * 60)
        print("CHYBĚJÍCÍ ZÁVISLOSTI")
        print("=" * 60)
        print("\nNásledující knihovny nejsou nainstalované:")
        for lib in missing:
            print(f"  - {lib}")
        print("\nNainstalujte je pomocí:")
        print(f"  pip install {' '.join(missing)}")
        print("\nNebo nainstalujte všechny závislosti:")
        print("  pip install -r requirements.txt")
        print("=" * 60)
        return False
    
    return True


def check_tesseract():
    """Check if Tesseract OCR is installed."""
    import pytesseract
    from src.config import get_config
    
    # Get configured path
    config = get_config()
    tesseract_path = config.get_tesseract_path()
    
    # Set the path before checking
    if tesseract_path and os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract OCR verze: {version}")
        print(f"   Cesta: {tesseract_path}")
        return True
    except Exception as e:
        print("=" * 60)
        print("TESSERACT OCR NENÍ DOSTUPNÝ")
        print("=" * 60)
        print(f"\nNastavená cesta: {tesseract_path}")
        if not os.path.exists(tesseract_path):
            print("⚠️  Soubor na této cestě NEEXISTUJE!")
        print("\nŘešení:")
        print("  1. Spusťte aplikaci a otevřete ⚙️ Nastavení")
        print("  2. Nastavte správnou cestu k tesseract.exe")
        print("  3. Klikněte na 'Otestovat připojení'")
        print("\nTypická cesta: C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
        print("=" * 60)
        return False


def main():
    """Main entry point."""
    print("=" * 60)
    print("  OCR DESKTOP APPLICATION v1.0.0")
    print("  Převod naskenovaných dokumentů na digitální text")
    print("=" * 60)
    print()
    
    # Check dependencies
    print("Kontrola závislostí...")
    if not check_dependencies():
        input("\nStiskněte Enter pro ukončení...")
        sys.exit(1)
    
    print("✅ Všechny závislosti jsou nainstalované")
    
    # Check Tesseract
    print("\nKontrola Tesseract OCR...")
    tesseract_ok = check_tesseract()
    
    if not tesseract_ok:
        print("\n⚠️ Aplikace se spustí, ale OCR nebude funkční.")
        print("   Nainstalujte Tesseract pro plnou funkčnost.")
    
    print("\nSpouštění aplikace...")
    print("-" * 60)
    
    # Import and run app
    from ui.app import run_app
    run_app()


if __name__ == "__main__":
    main()
