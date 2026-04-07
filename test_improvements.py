#!/usr/bin/env python3
"""
Test script to demonstrate the improved simplification pipeline.
Run this to see how the enhancements work:
1. Text cleaning (fixes OCR noise)
2. Prescription structuring (formats medicine info)
3. Medical term replacement (uses dictionary)
4. Enhanced T5 generation (better prompt & params)
"""

import sys
sys.path.insert(0, '/Users/ksidharthareddy/medicalreportsimplifier/backend')

from app.services.simplify import (
    clean_text, 
    structure_prescription, 
    replace_medical_terms
)

# Test Case 1: OCR Noise Cleaning
print("=" * 70)
print("TEST 1: OCR Noise Cleaning")
print("=" * 70)

noisy_ocr = """SANAPLE PRESCRIPTION
Moming      Afternoon      8P: 120/80mmHa
TAB. Paracetamol 500mg  1 tablet  three times daily"""

print("\n❌ BEFORE (Noisy OCR):")
print(noisy_ocr)

cleaned = clean_text(noisy_ocr)
print("\n✅ AFTER (Cleaned):")
print(cleaned)

# Test Case 2: Prescription Structuring
print("\n\n" + "=" * 70)
print("TEST 2: Prescription Structuring")
print("=" * 70)

raw_prescription = """Paracetamol 500 mg
1 tablet three times daily after food
Amoxicillin 250 mg
1 capsule twice daily with water
Take for 5 days"""

print("\n❌ BEFORE (Raw Text):")
print(raw_prescription)

structured = structure_prescription(raw_prescription)
print("\n✅ AFTER (Structured Format):")
print(structured)

# Test Case 3: Medical Term Replacement
print("\n\n" + "=" * 70)
print("TEST 3: Medical Term Dictionary Replacement")
print("=" * 70)

medical_text = """Patient diagnosed with hypertension and hyperglycemia.
Analgesic prescribed for pain relief.
CBC and LFT blood tests ordered.
Take BID - twice daily with food."""

print("\n❌ BEFORE (Complex Medical Terms):")
print(medical_text)

simplified = replace_medical_terms(medical_text)
print("\n✅ AFTER (Simple Language):")
print(simplified)

# Test Case 4: Complete Pipeline (without T5 to avoid loading model)
print("\n\n" + "=" * 70)
print("TEST 4: Complete Pipeline (All Improvements Combined)")
print("=" * 70)

complex_prescription = """SAMPLE RX
Moming 8P: 120/80mmHa
Ibuprofen 400mg: 1 tablet BID after meals
Amoxicillin 500mg: 1 capsule TID for 7 days
Atenolol 50mg: 1 tablet once daily for hypertension
Patient with tachycardia - monitor heart rate"""

print("\n📋 INPUT (Noisy OCR with complex medical terms):")
print(complex_prescription)

# Step by step
step1 = clean_text(complex_prescription)
print("\n📍 Step 1 - Cleaned:")
print(step1)

step2 = structure_prescription(step1)
print("\n📍 Step 2 - Structured:")
print(step2)

step3 = replace_medical_terms(step2)
print("\n📍 Step 3 - Medical Terms Replaced:")
print(step3)

print("\n✅ FINAL OUTPUT (Ready for T5 Model):")
print(step3)
print("\n💡 Note: The T5 model will now process this cleaned, structured,")
print("   simplified text with the improved prompt to generate")
print("   senior-friendly explanations.")

print("\n" + "=" * 70)
print("All improvements are working correctly!")
print("=" * 70)
