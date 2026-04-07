import pandas as pd
from transformers import (
    T5ForConditionalGeneration,
    T5Tokenizer,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)
from datasets import Dataset
import numpy as np

# ── 1. LARGE HIGH QUALITY DATASET ─────────────────────────
data = [
    # FEVER & VIRAL
    {
        "input": "simplify for patient: Patient presents with acute febrile illness with cephalgia and myalgia. Tab. Paracetamol 500mg tid pc for 5 days. Tab. Cetirizine 10mg hs for 5 days. Cap. Amoxicillin 250mg bid pc for 7 days. Adequate hydration and rest advised. Follow up after 5 days if symptoms persist.",
        "output": "You have a fever with headache and body pain caused by a viral infection.\n\nMedicines:\n• Paracetamol (fever and pain relief): 1 tablet, 3 times daily after food, for 5 days\n• Cetirizine (allergy/cold relief): 1 tablet at night, for 5 days\n• Amoxicillin (antibiotic): 1 capsule, 2 times daily after food, for 7 days\n\nAdvice: Drink plenty of water and rest well. Come back after 5 days if you still feel sick."
    },
    {
        "input": "simplify for patient: Diagnosis viral upper respiratory tract infection. Syp Paracetamol 10ml tid for 5 days. Tab Cetirizine 5mg od hs for 5 days. Steam inhalation bid. Avoid cold drinks. Review after 3 days.",
        "output": "You have a viral cold and throat infection.\n\nMedicines:\n• Paracetamol syrup (fever relief): 10ml, 3 times daily, for 5 days\n• Cetirizine (cold/allergy relief): 1 tablet at night, for 5 days\n\nAdvice: Do steam inhalation twice daily. Avoid cold drinks. Visit the doctor again after 3 days."
    },
    # BLOOD PRESSURE
    {
        "input": "simplify for patient: Patient has essential hypertension. BP 150/90 mmHg. Tab Amlodipine 5mg od morning. Tab Losartan 50mg od morning. Low sodium diet. Regular BP monitoring. Review after 1 month.",
        "output": "You have high blood pressure (150/90).\n\nMedicines:\n• Amlodipine (blood pressure medicine): 1 tablet every morning\n• Losartan (blood pressure medicine): 1 tablet every morning\n\nAdvice: Eat less salt. Check your blood pressure regularly. Come back after 1 month."
    },
    {
        "input": "simplify for patient: Hypertension with headache. Tab Atenolol 50mg od. Tab Hydrochlorothiazide 25mg od morning. Avoid stress. Exercise 30 min daily. Salt restriction. Follow up 2 weeks.",
        "output": "You have high blood pressure causing headaches.\n\nMedicines:\n• Atenolol (blood pressure medicine): 1 tablet once daily\n• Hydrochlorothiazide (water tablet to lower pressure): 1 tablet every morning\n\nAdvice: Avoid stress. Walk or exercise for 30 minutes daily. Eat less salt. Visit after 2 weeks."
    },
    # DIABETES
    {
        "input": "simplify for patient: Type 2 Diabetes Mellitus. FBS 180 mg/dl. Tab Metformin 500mg bid pc. Tab Glimepiride 1mg od before breakfast. HbA1c after 3 months. Diet control advised. Avoid sugar and sweets.",
        "output": "You have diabetes (your blood sugar is high at 180).\n\nMedicines:\n• Metformin (diabetes medicine): 1 tablet, 2 times daily after food\n• Glimepiride (diabetes medicine): 1 tablet before breakfast\n\nAdvice: Get a blood sugar test (HbA1c) after 3 months. Control your diet. Avoid sugar and sweets."
    },
    {
        "input": "simplify for patient: Diabetes with peripheral neuropathy. Tab Metformin 1000mg bid. Tab Pregabalin 75mg hs. Regular blood glucose monitoring. Foot care advised. Avoid walking barefoot.",
        "output": "You have diabetes with nerve pain in your hands and feet.\n\nMedicines:\n• Metformin (diabetes medicine): 1 tablet, 2 times daily\n• Pregabalin (nerve pain relief): 1 tablet at night\n\nAdvice: Check your blood sugar regularly. Take care of your feet. Never walk without footwear."
    },
    # STOMACH
    {
        "input": "simplify for patient: Acute gastroenteritis with vomiting and loose stools. Tab Ondansetron 4mg tid. Tab Metronidazole 400mg tid for 5 days. ORS 200ml after every loose stool. Bland diet. Avoid spicy oily food.",
        "output": "You have a stomach infection with vomiting and loose motions.\n\nMedicines:\n• Ondansetron (stops vomiting): 1 tablet, 3 times daily\n• Metronidazole (antibiotic for stomach): 1 tablet, 3 times daily for 5 days\n• ORS solution: Drink 1 glass (200ml) after every loose motion\n\nAdvice: Eat simple plain food. Avoid spicy and oily food."
    },
    {
        "input": "simplify for patient: Peptic ulcer disease with epigastric pain. Tab Omeprazole 20mg ac bid. Tab Sucralfate 1g qid. Avoid NSAIDs alcohol spicy food. Eat small frequent meals. Review after 4 weeks.",
        "output": "You have a painful sore (ulcer) in your stomach.\n\nMedicines:\n• Omeprazole (reduces stomach acid): 1 tablet, 2 times daily before meals\n• Sucralfate (protects stomach lining): 1 tablet, 4 times daily\n\nAdvice: Do not take painkillers like ibuprofen. Avoid alcohol and spicy food. Eat small meals frequently. Come back after 4 weeks."
    },
    # INFECTIONS
    {
        "input": "simplify for patient: Acute tonsillitis with odynophagia. Tab Amoxicillin 500mg tid for 7 days. Tab Ibuprofen 400mg tid pc for 3 days. Warm saline gargles qid. Cold fluids and ice cream allowed. Review after 5 days.",
        "output": "You have an infected and swollen throat (tonsils).\n\nMedicines:\n• Amoxicillin (antibiotic): 1 tablet, 3 times daily for 7 days\n• Ibuprofen (pain and swelling relief): 1 tablet, 3 times daily after food for 3 days\n\nAdvice: Gargle with warm salt water 4 times daily. You can have cold drinks and ice cream. Come back after 5 days."
    },
    {
        "input": "simplify for patient: Urinary tract infection with dysuria and frequency. Tab Ciprofloxacin 500mg bid for 5 days. Tab Phenazopyridine 200mg tid for 2 days. Increase fluid intake to 3L per day. Avoid caffeine. Urine culture after treatment.",
        "output": "You have a urine infection causing pain and frequent urination.\n\nMedicines:\n• Ciprofloxacin (antibiotic for urine infection): 1 tablet, 2 times daily for 5 days\n• Phenazopyridine (relieves burning sensation): 1 tablet, 3 times daily for 2 days\n\nAdvice: Drink at least 3 litres of water daily. Avoid tea and coffee. Get a urine test done after completing medicines."
    },
    # RESPIRATORY
    {
        "input": "simplify for patient: Acute bronchitis with productive cough. Tab Azithromycin 500mg od for 3 days. Syp Bromhexine 10ml tid. Tab Salbutamol 2mg tid. Steam inhalation bid. Avoid smoking and dust.",
        "output": "You have an infection in your airways with cough and phlegm.\n\nMedicines:\n• Azithromycin (antibiotic): 1 tablet once daily for 3 days\n• Bromhexine syrup (loosens phlegm): 10ml, 3 times daily\n• Salbutamol (opens airways): 1 tablet, 3 times daily\n\nAdvice: Do steam inhalation twice daily. Do not smoke. Avoid dusty places."
    },
    {
        "input": "simplify for patient: Bronchial asthma exacerbation. Budesonide inhaler 200mcg bid. Salbutamol inhaler 2 puffs prn. Tab Montelukast 10mg hs. Avoid cold air dust and smoke. Peak flow monitoring daily.",
        "output": "You have asthma that has become worse.\n\nMedicines:\n• Budesonide inhaler (reduces airway swelling): 2 puffs, 2 times daily\n• Salbutamol inhaler (emergency reliever): 2 puffs when breathing difficulty occurs\n• Montelukast (prevents asthma attacks): 1 tablet at night\n\nAdvice: Avoid cold air, dust, and smoke. Monitor your breathing daily with a peak flow meter."
    },
    # PAIN
    {
        "input": "simplify for patient: Migraine with photophobia and phonophobia. Tab Sumatriptan 50mg stat at onset. Tab Propranolol 40mg od for prevention. Avoid triggers like bright light loud noise stress and alcohol. Maintain headache diary.",
        "output": "You have migraine headaches with sensitivity to light and sound.\n\nMedicines:\n• Sumatriptan (stops migraine): Take 1 tablet immediately when headache starts\n• Propranolol (prevents migraines): 1 tablet once daily\n\nAdvice: Avoid triggers like bright lights, loud noises, stress, and alcohol. Write down when headaches happen and what caused them."
    },
    {
        "input": "simplify for patient: Low back pain with lumbar muscle spasm. Tab Diclofenac 50mg tid pc for 5 days. Tab Thiocolchicoside 4mg bid for 5 days. Hot fomentation tid. Physiotherapy advised. Avoid heavy lifting.",
        "output": "You have lower back pain with muscle tightness.\n\nMedicines:\n• Diclofenac (pain and inflammation relief): 1 tablet, 3 times daily after food for 5 days\n• Thiocolchicoside (muscle relaxer): 1 tablet, 2 times daily for 5 days\n\nAdvice: Apply a hot water bag 3 times daily. Do physiotherapy exercises. Do not lift heavy objects."
    },
    # SKIN
    {
        "input": "simplify for patient: Allergic dermatitis with pruritus. Tab Cetirizine 10mg od hs. Hydrocortisone cream apply bid to affected area. Avoid soap on rash. Wear cotton clothes. Avoid triggering allergen.",
        "output": "You have a skin allergy with itching and rash.\n\nMedicines:\n• Cetirizine (reduces allergy and itching): 1 tablet at night\n• Hydrocortisone cream (calms skin irritation): Apply on the rash 2 times daily\n\nAdvice: Do not use soap on the rash. Wear loose cotton clothes. Avoid whatever is causing the allergy."
    },
    {
        "input": "simplify for patient: Fungal skin infection tinea corporis. Clotrimazole cream apply bid for 4 weeks. Tab Fluconazole 150mg once weekly for 4 weeks. Keep skin dry. Avoid sharing towels and clothes.",
        "output": "You have a fungal skin infection (ringworm).\n\nMedicines:\n• Clotrimazole cream (antifungal): Apply on the affected skin 2 times daily for 4 weeks\n• Fluconazole tablet (antifungal): 1 tablet once every week for 4 weeks\n\nAdvice: Keep the affected area dry. Do not share towels or clothes with others."
    },
    # EYES
    {
        "input": "simplify for patient: Bacterial conjunctivitis with mucopurulent discharge. Tobramycin eye drops 1 drop qid for 7 days. Ciprofloxacin eye ointment hs. Clean eye with clean cotton. Avoid touching eyes. Do not share eye drops.",
        "output": "You have a bacterial eye infection (pink eye) with yellow discharge.\n\nMedicines:\n• Tobramycin eye drops (antibiotic): 1 drop in the infected eye, 4 times daily for 7 days\n• Ciprofloxacin eye ointment: Apply at night\n\nAdvice: Clean your eye gently with clean cotton. Do not touch or rub your eyes. Never share eye drops with anyone."
    },
    # HEART
    {
        "input": "simplify for patient: Stable angina pectoris. Tab Aspirin 75mg od after breakfast. Tab Atorvastatin 40mg hs. Tab Isosorbide mononitrate 30mg od. Sublingual GTN spray prn for chest pain. Avoid exertion. Cardiac diet advised.",
        "output": "You have chest pain due to reduced blood flow to your heart (angina).\n\nMedicines:\n• Aspirin (thins blood to prevent clots): 1 tablet after breakfast daily\n• Atorvastatin (lowers cholesterol): 1 tablet at night\n• Isosorbide mononitrate (prevents chest pain): 1 tablet once daily\n• GTN spray (emergency): Spray under tongue immediately if chest pain occurs\n\nAdvice: Do not over-exert yourself. Eat a heart-healthy diet low in fat and salt."
    },
    # THYROID
    {
        "input": "simplify for patient: Hypothyroidism TSH elevated 12 mIU/L. Tab Levothyroxine 50mcg od empty stomach. Avoid calcium and iron supplements within 4 hours. TSH after 6 weeks. Lifelong medication advised.",
        "output": "Your thyroid gland is underactive (TSH is high at 12).\n\nMedicines:\n• Levothyroxine (thyroid hormone): 1 tablet every morning on empty stomach\n\nAdvice: Do not take calcium or iron tablets within 4 hours of this medicine. Get a TSH blood test after 6 weeks. You will need to take this medicine lifelong."
    },
    # CHILDREN
    {
        "input": "simplify for patient: Child 5 years with fever cough and cold. Syp Paracetamol 5ml tid for 5 days. Syp Amoxicillin 5ml bid for 7 days. Syp Cetrizine 2.5ml od hs. Steam inhalation. Plenty of warm fluids.",
        "output": "Your child has fever, cough, and cold.\n\nMedicines (for child):\n• Paracetamol syrup (fever relief): 5ml, 3 times daily for 5 days\n• Amoxicillin syrup (antibiotic): 5ml, 2 times daily for 7 days\n• Cetirizine syrup (cold relief): 2.5ml at night\n\nAdvice: Give your child steam inhalation. Make sure the child drinks plenty of warm liquids like warm water and soup."
    },
    # GENERAL PRESCRIPTION FORMAT
    {
        "input": "simplify for patient: Patient Name Rahul Sharma Age 32 Date 12 March 2026 Diagnosis Patient presents with mild viral fever headache and body pain Prescription Tab Paracetamol 500 mg Dosage 1 tablet three times daily after food Duration 5 days Cap Amoxicillin 250 mg Dosage 1 capsule twice daily after food Duration 7 days Tab Cetirizine 10 mg Dosage 1 tablet at night Duration 5 days Advice Drink plenty of fluids and take adequate rest Avoid cold beverages and outside food Follow-up Visit again after 5 days if symptoms persist",
        "output": "Patient: Rahul Sharma | Age: 32\n\nWhat you have: You have a mild viral fever (infection) with headache and body pain.\n\nYour medicines:\n• Paracetamol 500mg (reduces fever and pain): Take 1 tablet, 3 times daily after food, for 5 days\n• Amoxicillin 250mg (antibiotic to fight infection): Take 1 capsule, 2 times daily after food, for 7 days\n• Cetirizine 10mg (relieves cold and allergy): Take 1 tablet at night, for 5 days\n\nWhat you should do:\n• Drink lots of water and other fluids\n• Take proper rest\n• Avoid cold drinks and outside food\n• Come back to the doctor after 5 days if you are still not feeling better"
    },
]

print(f"Total training pairs: {len(data)}")

# ── 2. Tokenize ───────────────────────────────────────────
tokenizer = T5Tokenizer.from_pretrained("t5-base")

def tokenize(batch):
    model_inputs = tokenizer(
        batch["input"],
        max_length=512,
        truncation=True,
        padding="max_length"
    )
    labels = tokenizer(
        batch["output"],
        max_length=256,
        truncation=True,
        padding="max_length"
    )
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

df = pd.DataFrame(data)
dataset = Dataset.from_pandas(df)
tokenized = dataset.map(tokenize, batched=True)

# ── 3. Model ──────────────────────────────────────────────
model = T5ForConditionalGeneration.from_pretrained("t5-base")
data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

# ── 4. Training ───────────────────────────────────────────
training_args = Seq2SeqTrainingArguments(
    output_dir="./models/t5-prescription",
    num_train_epochs=100,
    per_device_train_batch_size=2,
    learning_rate=5e-4,
    warmup_steps=50,
    logging_steps=20,
    save_steps=1000,
    predict_with_generate=True,
    fp16=False,
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=data_collator,
    tokenizer=tokenizer,
)

print("Training T5-base on medical prescriptions...")
trainer.train()

model.save_pretrained("./models/t5-prescription")
tokenizer.save_pretrained("./models/t5-prescription")
print("✅ Model saved to ./models/t5-prescription")
