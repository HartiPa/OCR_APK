from src.inference_engine import InferenceEngine

text = """
DODACÍ LIST
Číslo dokladu: 000360
Odběratel:
Firma ABC
IČ: 99999999
Dodavatel:
Firma XYZ
IČ: 12345678
Poznámka: telefon 12345678
"""

engine = InferenceEngine()

print("--- IČ Analysis (Supplier preferred) ---")
results = engine.analyze(text, 'ico', ['IČ'], preferred_section='supplier')
for r in results:
    print(f"Value: {r['value']}")
    print(f"  Score: {r['score']}")
    print(f"  Confidence: {r['confidence']}")
    print(f"  Debug: {r['debug']}")
    print("-" * 20)

print("\n--- IČ Analysis (Customer preferred) ---")
results = engine.analyze(text, 'ico', ['IČ'], preferred_section='customer')
for r in results:
    print(f"Value: {r['value']}")
    print(f"  Score: {r['score']}")

