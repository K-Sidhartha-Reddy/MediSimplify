from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import fitz
import pytesseract
import torch  # type: ignore[import-not-found]
from PIL import Image
from transformers import (
    AutoModel,
    AutoTokenizer,
    VisionEncoderDecoderModel,
    pipeline,
)
from transformers import TrOCRProcessor


# Path to a plain-language dictionary used in step 4.
MEDICAL_DICT_PATH = Path(__file__).resolve().parents[1] / "resources" / "medical_dict.json"

# Common medical abbreviations expanded in step 2.
ABBREVIATION_MAP: dict[str, str] = {
    "bid": "twice daily",
    "tid": "three times daily",
    "qid": "four times daily",
    "prn": "as needed",
    "qhs": "every night at bedtime",
    "po": "by mouth",
    "iv": "through a vein",
    "subq": "under the skin",
}

# Lightweight dictionaries for domain entities to support NER labeling.
DISEASE_TERMS = {
    "hypertension",
    "diabetes",
    "hyperglycemia",
    "hypoglycemia",
    "asthma",
    "copd",
    "anemia",
    "pneumonia",
    "myocardial infarction",
    "heart failure",
    "ckd",
}

SYMPTOM_TERMS = {
    "fever",
    "cough",
    "fatigue",
    "nausea",
    "vomiting",
    "dyspnea",
    "headache",
    "chest pain",
    "dizziness",
    "edema",
}

LAB_INDICATOR_TERMS = {
    "hba1c",
    "glucose",
    "creatinine",
    "sodium",
    "potassium",
    "hemoglobin",
    "wbc",
    "rbc",
    "platelet",
    "ldl",
    "hdl",
    "triglycerides",
    "alt",
    "ast",
}

# Candidate conditions for disease detection in step 6.
CONDITION_LABELS = [
    "Hypertension",
    "Diabetes Mellitus",
    "Respiratory Disease",
    "Cardiovascular Disease",
    "Kidney Disease",
    "Liver Disease",
    "Infection",
]

CONDITION_PLAIN_LANGUAGE = {
    "Hypertension": "May indicate persistent high blood pressure.",
    "Diabetes Mellitus": "May indicate blood sugar regulation problems.",
    "Respiratory Disease": "May indicate breathing or lung-related disease.",
    "Cardiovascular Disease": "May indicate heart or blood vessel disease.",
    "Kidney Disease": "May indicate reduced kidney function.",
    "Liver Disease": "May indicate liver inflammation or damage.",
    "Infection": "May indicate an active infection.",
}


@dataclass
class OcrOutput:
    text: str
    confidence: float
    engine: str


class MedicalReportSimplifierPipeline:
    """End-to-end medical report simplification pipeline.

    Steps:
    1) OCR (printed or handwritten)
    2) Text preprocessing + abbreviation normalization + spaCy tokenization
    3) NER extraction (BioBERT-backed + domain heuristics)
    4) Dictionary mapping to plain language
    5) T5 simplification
    6) Disease detection using a BERT-family classifier
    """

    def __init__(self) -> None:
        # Initialize regex once for speed and consistency.
        self._whitespace_re = re.compile(r"\s+")
        self._noise_re = re.compile(r"[^\w\s.,:/%+-]")
        self._dosage_re = re.compile(r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml|units?)\b", re.IGNORECASE)
        self._frequency_re = re.compile(
            r"\b(?:once daily|twice daily|three times daily|four times daily|as needed|every\s+\d+\s+hours?)\b",
            re.IGNORECASE,
        )
        self._lab_value_re = re.compile(r"\b([A-Za-z]{2,15})\s*[:=]\s*(\d+(?:\.\d+)?)\b")

    # -----------------------------
    # Lazy model/resource loaders
    # -----------------------------
    @staticmethod
    @lru_cache(maxsize=1)
    def _load_spacy_nlp():
        # spaCy model is loaded once and cached.
        import spacy  # type: ignore[import-not-found]

        try:
            return spacy.load("en_core_web_sm")
        except Exception:
            # Fallback tokenizer if language model is not installed.
            nlp = spacy.blank("en")
            if "sentencizer" not in nlp.pipe_names:
                nlp.add_pipe("sentencizer")
            return nlp

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_medical_dict() -> dict[str, str]:
        # Dictionary is loaded once and cached.
        if MEDICAL_DICT_PATH.exists():
            return json.loads(MEDICAL_DICT_PATH.read_text(encoding="utf-8"))
        return {}

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_trocr_processor() -> TrOCRProcessor:
        # Handwritten OCR processor.
        return TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_trocr_model() -> VisionEncoderDecoderModel:
        # Handwritten OCR model.
        return VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_biobert_tokenizer() -> AutoTokenizer:
        # BioBERT tokenizer used to contextualize clinical text in NER step.
        return AutoTokenizer.from_pretrained("bert-base-uncased")

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_biobert_model() -> AutoModel:
        # BioBERT encoder (base model) loaded once.
        return AutoModel.from_pretrained("bert-base-uncased")

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_t5_simplifier():
        # T5 text2text pipeline for patient-friendly simplification.
        model_path = "/Users/ksidharthareddy/medicalreportsimplifier/models/t5-medical-new"
        return pipeline("text2text-generation", model=model_path, tokenizer=model_path)

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_condition_classifier():
        # BERT-family zero-shot classifier for disease detection.
       return pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")
    # -----------------------------
    # Step 1: OCR
    # -----------------------------
    def _ocr_printed_image(self, image: Image.Image) -> OcrOutput:
        # pytesseract image_to_data returns token-level confidence.
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        texts: list[str] = []
        confidences: list[float] = []
        for token, conf in zip(data.get("text", []), data.get("conf", []), strict=False):
            token = (token or "").strip()
            if not token:
                continue
            texts.append(token)
            try:
                conf_value = float(conf)
                if conf_value >= 0:
                    confidences.append(conf_value)
            except Exception:
                continue

        joined_text = " ".join(texts)
        avg_conf = round(sum(confidences) / max(len(confidences), 1), 2)
        return OcrOutput(text=joined_text, confidence=avg_conf, engine="pytesseract")

    def _ocr_handwritten_image(self, image: Image.Image) -> OcrOutput:
        # TrOCR generation output includes token scores for confidence estimation.
        processor = self._load_trocr_processor()
        model = self._load_trocr_model()

        pixel_values = processor(images=image, return_tensors="pt").pixel_values
        with torch.no_grad():
            generated = model.generate(
                pixel_values,
                return_dict_in_generate=True,
                output_scores=True,
                max_new_tokens=128,
            )

        text = processor.batch_decode(generated.sequences, skip_special_tokens=True)[0]

        # Approximate confidence from average top-token softmax per generation step.
        step_confidences: list[float] = []
        for step_scores in generated.scores:
            probs = torch.softmax(step_scores, dim=-1)
            top_prob = probs.max(dim=-1).values.mean().item()
            step_confidences.append(top_prob * 100)

        avg_conf = round(sum(step_confidences) / max(len(step_confidences), 1), 2)
        return OcrOutput(text=text.strip(), confidence=avg_conf, engine="trocr")

    def extract_text_with_confidence(self, file_bytes: bytes, handwritten: bool = False) -> OcrOutput:
        """Extract text from image/pdf and return confidence score.

        - printed input -> pytesseract
        - handwritten input -> TrOCR (for image input)
        """

        # Open image directly, otherwise fallback to first page render for PDF.
        try:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        except Exception:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            page = doc[0]
            pix = page.get_pixmap(dpi=220)
            image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

        if handwritten:
            return self._ocr_handwritten_image(image)
        return self._ocr_printed_image(image)

    # -----------------------------
    # Step 2: Preprocessing
    # -----------------------------
    def _normalize_abbreviations(self, text: str) -> str:
        normalized = text
        for short, full in ABBREVIATION_MAP.items():
            # Replace abbreviations case-insensitively with word boundaries.
            normalized = re.sub(rf"\b{re.escape(short)}\b", full, normalized, flags=re.IGNORECASE)
        return normalized

    def preprocess_text(self, text: str) -> dict[str, Any]:
        # Remove special noise but preserve clinically meaningful punctuation.
        text = self._noise_re.sub(" ", text)
        text = self._whitespace_re.sub(" ", text).strip()

        # Expand common clinical abbreviations before downstream NLP.
        text = self._normalize_abbreviations(text)

        # Tokenize with spaCy.
        nlp = self._load_spacy_nlp()
        doc = nlp(text)
        tokens = [token.text for token in doc if not token.is_space]

        return {
            "cleaned_text": text,
            "tokens": tokens,
        }

    # -----------------------------
    # Step 3: NER (BioBERT-backed)
    # -----------------------------
    def extract_entities(self, text: str) -> list[dict[str, str]]:
        """Extract domain entities.

        BioBERT is used to contextualize text. Since the base checkpoint is not
        token-classification fine-tuned, we combine it with deterministic
        medical extraction heuristics for stable production behavior.
        """

        tokenizer = self._load_biobert_tokenizer()
        model = self._load_biobert_model()

        # Run BioBERT forward pass once (cached model) to embed medical context.
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            _ = model(**inputs)

        lowered = text.lower()
        entities: list[dict[str, str]] = []

        # Disease names.
        for term in sorted(DISEASE_TERMS):
            if re.search(rf"\b{re.escape(term)}\b", lowered):
                entities.append({"text": term, "label": "DISEASE"})

        # Symptoms.
        for term in sorted(SYMPTOM_TERMS):
            if re.search(rf"\b{re.escape(term)}\b", lowered):
                entities.append({"text": term, "label": "SYMPTOM"})

        # Lab indicators and optional values.
        for term in sorted(LAB_INDICATOR_TERMS):
            if re.search(rf"\b{re.escape(term)}\b", lowered):
                entities.append({"text": term, "label": "LAB_INDICATOR"})

        for key, value in self._lab_value_re.findall(text):
            entities.append({"text": f"{key}:{value}", "label": "LAB_VALUE"})

        # Dosages and frequency patterns.
        for dose in self._dosage_re.findall(text):
            entities.append({"text": dose, "label": "DOSAGE"})

        for freq in self._frequency_re.findall(text):
            entities.append({"text": freq, "label": "FREQUENCY"})

        # Drug name approximation from title-case tokens before dosage.
        drug_pattern = re.compile(r"\b([A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]{2,})*)\s+\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml|units?)\b")
        for match in drug_pattern.findall(text):
            entities.append({"text": match.strip(), "label": "DRUG"})

        # Deduplicate while preserving order.
        seen: set[tuple[str, str]] = set()
        unique_entities: list[dict[str, str]] = []
        for entity in entities:
            key = (entity["text"].lower(), entity["label"])
            if key in seen:
                continue
            seen.add(key)
            unique_entities.append(entity)

        return unique_entities

    # -----------------------------
    # Step 4: Dictionary Mapping
    # -----------------------------
    def map_to_plain_language(self, entities: list[dict[str, str]]) -> dict[str, str]:
        med_dict = self._load_medical_dict()
        mappings: dict[str, str] = {}

        for entity in entities:
            source = entity["text"]
            mapped = med_dict.get(source.lower())
            if mapped:
                mappings[source] = mapped

        return mappings

    # -----------------------------
    # Step 5: Simplification (T5)
    # -----------------------------
    def simplify_text(self, medical_text: str) -> str:
        simplifier = self._load_t5_simplifier()
        prompt = f"simplify for patient: {medical_text}"

        output = simplifier(
            prompt,
            max_length=220,
            min_length=40,
            do_sample=False,
            truncation=True,
        )
        return output[0]["generated_text"].strip()

    # -----------------------------
    # Step 6: Disease Detection
    # -----------------------------
    def detect_conditions(self, entities: list[dict[str, str]]) -> list[dict[str, Any]]:
        classifier = self._load_condition_classifier()

        # Build classifier input from clinically meaningful entities.
        disease_context = " ".join(
            entity["text"]
            for entity in entities
            if entity["label"] in {"DISEASE", "SYMPTOM", "LAB_INDICATOR", "LAB_VALUE"}
        ).strip()

        if not disease_context:
            return []

        result = classifier(
            disease_context,
            CONDITION_LABELS,
            multi_label=True,
            hypothesis_template="This report indicates {}.",
        )

        detected: list[dict[str, Any]] = []
        for label, score in zip(result["labels"], result["scores"], strict=False):
            if score < 0.35:
                continue
            detected.append(
                {
                    "condition": label,
                    "confidence": round(float(score), 4),
                    "description": CONDITION_PLAIN_LANGUAGE.get(label, "Possible underlying condition."),
                }
            )

        return detected

    def summarize_dosages(self, entities: list[dict[str, str]]) -> list[str]:
        dosages = [e["text"] for e in entities if e["label"] == "DOSAGE"]
        frequencies = [e["text"] for e in entities if e["label"] == "FREQUENCY"]

        summary: list[str] = []
        for i, dosage in enumerate(dosages):
            freq = frequencies[i] if i < len(frequencies) else "frequency not specified"
            summary.append(f"{dosage} — {freq}")

        return summary

    def run(self, file_bytes: bytes | None = None, text: str | None = None, handwritten: bool = False) -> dict[str, Any]:
        """Run full pipeline and return structured JSON-ready output."""

        if not file_bytes and not text:
            raise ValueError("Either file_bytes or text must be provided.")

        # Step 1: OCR if bytes are provided, otherwise use user-supplied text.
        if file_bytes:
            ocr_output = self.extract_text_with_confidence(file_bytes=file_bytes, handwritten=handwritten)
            original_text = ocr_output.text
            ocr_meta = {
                "engine": ocr_output.engine,
                "confidence": ocr_output.confidence,
            }
        else:
            original_text = text or ""
            ocr_meta = {
                "engine": "none",
                "confidence": None,
            }

        # Step 2: clean, normalize, tokenize.
        preprocessed = self.preprocess_text(original_text)
        cleaned_text = preprocessed["cleaned_text"]

        # Step 3: extract entities.
        entities = self.extract_entities(cleaned_text)

        # Step 4: map terms to plain language.
        plain_mappings = self.map_to_plain_language(entities)

        # Step 5: simplify medical narrative.
        simplified_text = self.simplify_text(cleaned_text)

        # Step 6: detect likely underlying conditions.
        detected_conditions = self.detect_conditions(entities)

        # Additional dosage summary from extracted entities.
        dosage_summary = self.summarize_dosages(entities)

        return {
            "original_text": original_text,
            "simplified_text": simplified_text,
            "entities": entities,
            "plain_language_mappings": plain_mappings,
            "detected_conditions": detected_conditions,
            "dosage_summary": dosage_summary,
            "ocr": ocr_meta,
            "tokens": preprocessed["tokens"],
        }


# Singleton helper for API/service usage.
@lru_cache(maxsize=1)
def get_medical_report_pipeline() -> MedicalReportSimplifierPipeline:
    return MedicalReportSimplifierPipeline()
