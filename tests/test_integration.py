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
"""

fields = {
    "IČ dodavatele": "IČ",
    "IČ odběratele": "IČ",
    "Datum vystavení": "datum",
    "Neznámé pole": "něco"
}

print("--- Simulating Mode B Logic ---")
inference = InferenceEngine()
results = {}

for field_name, example in fields.items():
    field_lower = field_name.lower()
    example_lower = example.lower()
    
    # Logic copied from ModeBView
    field_type = 'general'
    if any(x in field_lower or x in example_lower for x in ['ič', 'ico', 'ičo']):
        field_type = 'ico'
    elif any(x in field_lower or x in example_lower for x in ['dič', 'dic']):
        field_type = 'dic'
    # ... (other types)
    
    section = None
    if 'dodavatel' in field_lower:
        section = 'supplier'
    elif 'odběratel' in field_lower:
        section = 'customer'
        
    print(f"Field: {field_name} -> Type: {field_type}, Section: {section}")
    
    if field_type != 'general':
        best = inference.find_best(text, field_type, [field_name, example], preferred_section=section)
        if best:
            print(f"  Result: {best['value']} (Score: {best['score']})")
        else:
            print("  Result: None")
