#!/usr/bin/env python3
"""
Test Script for Scanned Document OCR Extraction
Tests all files in sken/JPG and sken/PDF folders for:
1. Correct extraction of delivery note information
2. Repeatability across multiple runs
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image
from src.ocr_engine import OCREngine
from src.pattern_matcher import PatternMatcher
from src.pdf_handler import pdf_to_images, is_pdf_file, is_image_file

# Number of iterations for repeatability test
NUM_ITERATIONS = 3


def extract_document_data(image: Image.Image, ocr_engine: OCREngine) -> Dict[str, Any]:
    """Extract delivery note data from a single image."""
    # Get raw text
    text = ocr_engine.extract_text_from_image(image)

    # Use pattern matcher to extract structured data
    matcher = PatternMatcher()
    result = matcher.extract_delivery_note(text)
    result['raw_text_length'] = len(text)
    result['raw_text_preview'] = text[:500] if text else ""

    return result


def process_file(file_path: str, ocr_engine: OCREngine) -> Dict[str, Any]:
    """Process a single file (PDF or image) and extract data."""
    results = {
        'file': os.path.basename(file_path),
        'file_path': file_path,
        'pages': []
    }

    if is_pdf_file(file_path):
        # Convert PDF to images
        images = pdf_to_images(file_path, dpi=200)
        for i, img in enumerate(images):
            page_data = extract_document_data(img, ocr_engine)
            page_data['page_number'] = i + 1
            results['pages'].append(page_data)
    elif is_image_file(file_path):
        img = Image.open(file_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        page_data = extract_document_data(img, ocr_engine)
        page_data['page_number'] = 1
        results['pages'].append(page_data)

    return results


def compare_results(result1: Dict, result2: Dict) -> Tuple[bool, List[str]]:
    """Compare two extraction results for equality."""
    differences = []

    # Compare key fields
    fields_to_compare = ['cislo_dokladu', 'objednavka', 'datum_porizeni',
                         'dodavatel_ic', 'dodavatel_dic']

    for page_idx, (p1, p2) in enumerate(zip(result1['pages'], result2['pages'])):
        for field in fields_to_compare:
            v1 = p1.get(field)
            v2 = p2.get(field)
            if v1 != v2:
                differences.append(f"Page {page_idx + 1}, {field}: '{v1}' vs '{v2}'")

        # Compare items count
        items1 = len(p1.get('polozky', []))
        items2 = len(p2.get('polozky', []))
        if items1 != items2:
            differences.append(f"Page {page_idx + 1}, items count: {items1} vs {items2}")

    return len(differences) == 0, differences


def run_tests() -> Dict[str, Any]:
    """Run tests on all scanned documents."""
    print("=" * 70)
    print("  OCR EXTRACTION TEST FOR SCANNED DOCUMENTS")
    print("=" * 70)
    print()

    # Initialize OCR engine
    print("Initializing OCR engine...")
    try:
        ocr_engine = OCREngine(tesseract_path=None, language="ces+eng")
        print("  OK - OCR engine initialized\n")
    except Exception as e:
        print(f"  ERROR: Failed to initialize OCR engine: {e}")
        return {'error': str(e)}

    # Find all test files
    base_dir = Path(__file__).parent
    jpg_dir = base_dir / 'sken' / 'JPG'
    pdf_dir = base_dir / 'sken' / 'PDF'

    test_files = []

    if jpg_dir.exists():
        test_files.extend(sorted(jpg_dir.glob('*.jpg')))
    if pdf_dir.exists():
        test_files.extend(sorted(pdf_dir.glob('*.pdf')))

    print(f"Found {len(test_files)} test files:")
    print(f"  - JPG: {len([f for f in test_files if str(f).endswith('.jpg')])}")
    print(f"  - PDF: {len([f for f in test_files if str(f).endswith('.pdf')])}")
    print()

    # Run tests
    all_results = {
        'test_date': datetime.now().isoformat(),
        'num_iterations': NUM_ITERATIONS,
        'files': {}
    }

    total_files = len(test_files)
    passed_extraction = 0
    passed_repeatability = 0

    for file_idx, file_path in enumerate(test_files):
        file_name = file_path.name
        print(f"[{file_idx + 1}/{total_files}] Testing: {file_name}")

        file_results = {
            'iterations': [],
            'extraction_success': False,
            'repeatability': False,
            'differences': []
        }

        try:
            # Run multiple iterations
            for iteration in range(NUM_ITERATIONS):
                result = process_file(str(file_path), ocr_engine)
                file_results['iterations'].append(result)

            # Check if extraction found any data
            first_result = file_results['iterations'][0]
            has_data = False
            for page in first_result['pages']:
                if page.get('cislo_dokladu') or page.get('dodavatel_ic') or page.get('polozky'):
                    has_data = True
                    break

            file_results['extraction_success'] = has_data
            if has_data:
                passed_extraction += 1
                print(f"    Extraction: PASS")
            else:
                print(f"    Extraction: WARN (no key data found)")

            # Check repeatability
            all_same = True
            for i in range(1, NUM_ITERATIONS):
                is_same, diffs = compare_results(
                    file_results['iterations'][0],
                    file_results['iterations'][i]
                )
                if not is_same:
                    all_same = False
                    file_results['differences'].extend([f"Iter {i+1}: {d}" for d in diffs])

            file_results['repeatability'] = all_same
            if all_same:
                passed_repeatability += 1
                print(f"    Repeatability: PASS ({NUM_ITERATIONS} iterations identical)")
            else:
                print(f"    Repeatability: FAIL")
                for diff in file_results['differences'][:3]:
                    print(f"      - {diff}")

            # Print extracted data summary
            for page in first_result['pages']:
                print(f"    Page {page.get('page_number', 1)}:")
                if page.get('cislo_dokladu'):
                    print(f"      Cislo dokladu: {page['cislo_dokladu']}")
                if page.get('objednavka'):
                    print(f"      Objednavka: {page['objednavka']}")
                if page.get('datum_porizeni'):
                    print(f"      Datum porizeni: {page['datum_porizeni']}")
                if page.get('dodavatel_ic'):
                    print(f"      IC dodavatele: {page['dodavatel_ic']}")
                if page.get('dodavatel_dic'):
                    print(f"      DIC dodavatele: {page['dodavatel_dic']}")
                items_count = len(page.get('polozky', []))
                if items_count:
                    print(f"      Polozky: {items_count} items")

        except Exception as e:
            print(f"    ERROR: {e}")
            file_results['error'] = str(e)

        all_results['files'][file_name] = file_results
        print()

    # Summary
    print("=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print(f"  Total files tested: {total_files}")
    print(f"  Extraction success: {passed_extraction}/{total_files} ({100*passed_extraction/total_files:.1f}%)")
    print(f"  Repeatability pass: {passed_repeatability}/{total_files} ({100*passed_repeatability/total_files:.1f}%)")
    print()

    all_results['summary'] = {
        'total_files': total_files,
        'extraction_success': passed_extraction,
        'repeatability_pass': passed_repeatability
    }

    # Save detailed results to JSON
    results_file = base_dir / 'test_results.json'

    # Prepare results for JSON (remove raw text to keep file smaller)
    json_results = {
        'test_date': all_results['test_date'],
        'num_iterations': all_results['num_iterations'],
        'summary': all_results['summary'],
        'files': {}
    }

    for file_name, file_data in all_results['files'].items():
        json_results['files'][file_name] = {
            'extraction_success': file_data['extraction_success'],
            'repeatability': file_data['repeatability'],
            'differences': file_data['differences'],
            'extracted_data': {}
        }

        if file_data['iterations']:
            first_iter = file_data['iterations'][0]
            for page in first_iter['pages']:
                page_key = f"page_{page.get('page_number', 1)}"
                json_results['files'][file_name]['extracted_data'][page_key] = {
                    'cislo_dokladu': page.get('cislo_dokladu'),
                    'objednavka': page.get('objednavka'),
                    'datum_porizeni': page.get('datum_porizeni'),
                    'dodavatel_ic': page.get('dodavatel_ic'),
                    'dodavatel_dic': page.get('dodavatel_dic'),
                    'dodavatel_nazev': page.get('dodavatel_nazev'),
                    'polozky_count': len(page.get('polozky', [])),
                    'polozky': page.get('polozky', [])[:5]  # First 5 items
                }

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)

    print(f"  Detailed results saved to: {results_file}")
    print("=" * 70)

    return all_results


if __name__ == '__main__':
    results = run_tests()
