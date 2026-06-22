import os
import re
import json
from typing import List, Dict, Optional

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# =========================
# LOAD ENV + INIT LLM
# =========================
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY not found. Please set it in your .env file.")

llm = ChatOpenAI(
    model="gpt-4.1",
    api_key=API_KEY,
    temperature=0
)

# =========================
# HELPERS
# =========================
def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s,/+\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_field(text: str, field_name: str) -> str:
    pattern = rf"^{re.escape(field_name)}\s*:\s*(.*)$"
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_value_from_doc(text: str, field_name: str) -> str:
    pattern = rf"^{re.escape(field_name)}\s*:\s*(.*)$"
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else "Not available"


def token_match(query: str, target: str) -> bool:
    q = normalize_text(query)
    t = normalize_text(target)

    if not q or not t:
        return False

    if q == t:
        return True

    target_parts = re.split(r"[,/;|]", t)
    target_parts = [x.strip() for x in target_parts if x.strip()]

    if q in target_parts:
        return True

    target_words = set(t.split())
    if q in target_words:
        return True

    return q in t or t in q


# =========================
# DRUG ALIASES / CLASS MAP
# =========================
DRUG_CLASS_ALIASES = {
    "warfarin": ["coumadin", "anticoagulant", "anticoagulant / antiplatelet drugs", "blood thinner", "blood thinners"],
    "coumadin": ["warfarin", "anticoagulant", "anticoagulant / antiplatelet drugs", "blood thinner", "blood thinners"],

    "aspirin": ["antiplatelet", "anticoagulant / antiplatelet drugs", "blood thinner", "blood thinners"],
    "clopidogrel": ["plavix", "antiplatelet", "anticoagulant / antiplatelet drugs", "blood thinner", "blood thinners"],
    "plavix": ["clopidogrel", "antiplatelet", "anticoagulant / antiplatelet drugs", "blood thinner", "blood thinners"],

    "heparin": ["anticoagulant", "blood thinner", "blood thinners"],
    "apixaban": ["anticoagulant", "blood thinner", "blood thinners"],
    "rivaroxaban": ["anticoagulant", "blood thinner", "blood thinners"],
    "dabigatran": ["anticoagulant", "blood thinner", "blood thinners"],
    "enoxaparin": ["lovenox", "anticoagulant", "blood thinner", "blood thinners"],
    "lovenox": ["enoxaparin", "anticoagulant", "blood thinner", "blood thinners"],

    "metformin": ["antidiabetes drugs", "antidiabetic agents", "diabetes medications"],
    "insulin": ["antidiabetes drugs", "antidiabetic agents", "diabetes medications"],
}


def build_drug_query_variants(user_drug_name: str, normalized_drug: str, detected_drug_class: str, brand_name: str) -> List[str]:
    variants = []

    def add(v: str):
        v = v.strip() if v else ""
        if v and v.lower() != "not available" and v not in variants:
            variants.append(v)

    add(normalized_drug)
    add(user_drug_name)
    add(brand_name)

    nd = normalize_text(normalized_drug)
    ud = normalize_text(user_drug_name)

    if nd in DRUG_CLASS_ALIASES:
        for x in DRUG_CLASS_ALIASES[nd]:
            add(x)

    if ud in DRUG_CLASS_ALIASES:
        for x in DRUG_CLASS_ALIASES[ud]:
            add(x)

    add(detected_drug_class)
    return variants


# =========================
# PARSE HERB TEXT FILE
# =========================
def parse_herb_text_file(file_path: str) -> List[Document]:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    herb_blocks = re.split(r"(?=^\s*\d+\)\s*$)", text, flags=re.MULTILINE)

    documents = []

    for block in herb_blocks:
        if not block.strip():
            continue

        if not re.search(r"^\s*Primary Name\s*:", block, re.IGNORECASE | re.MULTILINE):
            continue

        primary_name = extract_field(block, "Primary Name")
        canonical_name = extract_field(block, "Canonical Name")
        system = extract_field(block, "System")
        indian_names = extract_field(block, "Indian/Common Names")
        english_names = extract_field(block, "English Names")
        botanical_names = extract_field(block, "Botanical Names")
        aliases = extract_field(block, "Normalized Search Aliases")

        interaction_blocks = re.split(
            r"(?=^\s*Interaction\s+\d+\s*$)",
            block,
            flags=re.IGNORECASE | re.MULTILINE
        )

        for interaction_block in interaction_blocks:
            if not interaction_block.strip():
                continue

            if not re.search(r"^\s*Interaction\s+\d+\s*$", interaction_block, re.IGNORECASE | re.MULTILINE):
                continue

            severity = extract_field(interaction_block, "Severity")
            drug = extract_field(interaction_block, "Drug")
            drug_type = extract_field(interaction_block, "Drug Type")
            drug_class = extract_field(interaction_block, "Drug Class")
            brand_names = extract_field(interaction_block, "Brand Names")
            mechanism = extract_field(interaction_block, "Mechanism")
            clinical_effect = extract_field(interaction_block, "Clinical Effect")
            recommendation = extract_field(interaction_block, "Recommendation")
            evidence_text = extract_field(interaction_block, "Evidence Text")

            if not drug and not drug_class and not brand_names:
                continue

            page_content = f"""
Herb: {primary_name}
Canonical Name: {canonical_name}
System: {system}
Indian/Common Names: {indian_names}
English Names: {english_names}
Botanical Names: {botanical_names}
Aliases: {aliases}

Interaction Drug: {drug}
Drug Type: {drug_type}
Drug Class: {drug_class}
Brand Names: {brand_names}
Severity: {severity}
Mechanism: {mechanism}
Clinical Effect: {clinical_effect}
Recommendation: {recommendation}
Evidence Text: {evidence_text}
""".strip()

            metadata = {
                "primary_name": primary_name,
                "canonical_name": canonical_name,
                "system": system,
                "indian_names": indian_names,
                "english_names": english_names,
                "botanical_names": botanical_names,
                "aliases": aliases,
                "drug": drug,
                "drug_type": drug_type,
                "drug_class": drug_class,
                "brand_names": brand_names,
                "severity": severity,
            }

            documents.append(Document(page_content=page_content, metadata=metadata))

    return documents


# =========================
# LLM: NORMALIZE DRUG
# =========================
def safe_json_parse(content: str) -> Dict:
    if not content:
        return {}

    content = content.strip()
    content = re.sub(r"^```json\s*|\s*```$", "", content, flags=re.IGNORECASE | re.DOTALL).strip()

    try:
        return json.loads(content)
    except Exception:
        pass

    try:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass

    return {}


def detect_drug_info_with_llm(drug_input: str) -> dict:
    prompt = ChatPromptTemplate.from_template("""
You are a medical drug normalization assistant.

Given a user-entered drug name, identify:
1. The normalized generic drug name
2. The brand name if the input is a brand
3. The drug class
4. The therapeutic category

Return ONLY valid JSON in this exact format:
{{
  "input_drug": "<original user input>",
  "normalized_drug_name": "<generic drug name>",
  "brand_name": "<brand name or Not available>",
  "drug_class": "<drug class>",
  "therapeutic_category": "<therapeutic category>"
}}

Rules:
- If input is a brand name, convert to generic name.
- If input is already a generic drug, keep it.
- If uncertain, return best-known standard medical mapping.
- Do not include markdown.
- Do not include explanation.

Drug input:
{drug_input}
""")

    chain = prompt | llm
    response = chain.invoke({"drug_input": drug_input})
    parsed = safe_json_parse(response.content)

    if not parsed:
        return {
            "input_drug": drug_input,
            "normalized_drug_name": drug_input,
            "brand_name": "Not available",
            "drug_class": "Not available",
            "therapeutic_category": "Not available"
        }

    return {
        "input_drug": parsed.get("input_drug", drug_input),
        "normalized_drug_name": parsed.get("normalized_drug_name", drug_input),
        "brand_name": parsed.get("brand_name", "Not available"),
        "drug_class": parsed.get("drug_class", "Not available"),
        "therapeutic_category": parsed.get("therapeutic_category", "Not available")
    }


# =========================
# MATCHING
# =========================
def score_herb_match(supplement_name: str, doc: Document) -> int:
    herb_q = normalize_text(supplement_name)

    primary_name = doc.metadata.get("primary_name", "")
    canonical_name = doc.metadata.get("canonical_name", "")
    indian_names = doc.metadata.get("indian_names", "")
    english_names = doc.metadata.get("english_names", "")
    botanical_names = doc.metadata.get("botanical_names", "")
    aliases = doc.metadata.get("aliases", "")

    if token_match(herb_q, primary_name):
        return 100
    if token_match(herb_q, canonical_name):
        return 90
    if token_match(herb_q, aliases):
        return 80
    if token_match(herb_q, indian_names):
        return 70
    if token_match(herb_q, english_names):
        return 60
    if token_match(herb_q, botanical_names):
        return 50

    return 0


def score_drug_match(user_drug_name: str, normalized_drug: str, detected_drug_class: str, brand_name: str, doc: Document) -> int:
    doc_drug = doc.metadata.get("drug", "")
    doc_brand = doc.metadata.get("brand_names", "")
    doc_class = doc.metadata.get("drug_class", "")

    if normalized_drug and normalized_drug != "Not available" and token_match(normalized_drug, doc_drug):
        return 100

    if user_drug_name and user_drug_name != "Not available" and token_match(user_drug_name, doc_drug):
        return 95

    if brand_name and brand_name != "Not available":
        if token_match(brand_name, doc_brand):
            return 90
        if token_match(brand_name, doc_drug):
            return 88

    variants = build_drug_query_variants(user_drug_name, normalized_drug, detected_drug_class, brand_name)
    for v in variants:
        if token_match(v, doc_drug):
            return 85
        if token_match(v, doc_brand):
            return 80

    if detected_drug_class and detected_drug_class != "Not available" and token_match(detected_drug_class, doc_class):
        return 60

    return 0


def find_best_interaction_for_pair(
    docs: List[Document],
    supplement_name: str,
    user_drug_name: str,
    normalized_drug: str,
    detected_drug_class: str,
    brand_name: str
) -> Optional[Document]:
    candidates = []

    for doc in docs:
        herb_score = score_herb_match(supplement_name, doc)
        if herb_score == 0:
            continue

        drug_score = score_drug_match(
            user_drug_name=user_drug_name,
            normalized_drug=normalized_drug,
            detected_drug_class=detected_drug_class,
            brand_name=brand_name,
            doc=doc
        )

        if drug_score == 0:
            continue

        total_score = herb_score + drug_score
        candidates.append((total_score, drug_score, herb_score, doc))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    return candidates[0][3]


def format_interaction_result(
    matched_doc: Document,
    supplement_name: str,
    user_drug_name: str,
    normalized_drug: str,
    detected_drug_class: str,
    therapeutic_category: str
) -> Dict:
    text = matched_doc.page_content

    return {
        "status": "found",
        "input_supplement": supplement_name,
        "input_drug": user_drug_name,
        "ayurvedic_name": extract_value_from_doc(text, "Herb"),
        "canonical_name": extract_value_from_doc(text, "Canonical Name"),
        "normalized_drug_name": normalized_drug,
        "allopathic_drug_name": extract_value_from_doc(text, "Interaction Drug"),
        "drug_type": extract_value_from_doc(text, "Drug Type"),
        "drug_class": extract_value_from_doc(text, "Drug Class"),
        "detected_drug_class": detected_drug_class,
        "therapeutic_category": therapeutic_category,
        "brand_names": extract_value_from_doc(text, "Brand Names"),
        "interaction_severity": extract_value_from_doc(text, "Severity"),
        "mechanism": extract_value_from_doc(text, "Mechanism"),
        "clinical_effect": extract_value_from_doc(text, "Clinical Effect"),
        "recommendation": extract_value_from_doc(text, "Recommendation"),
        "evidence_text": extract_value_from_doc(text, "Evidence Text")
    }


# =========================
# BULK REGISTRATION CHECK
# =========================
def check_registration_interactions(docs: List[Document], drugs: List[str], supplements: List[str]) -> Dict:
    interactions = []
    no_interactions = []

    # Normalize input lists
    drugs = [d.strip() for d in drugs if d and d.strip()]
    supplements = [s.strip() for s in supplements if s and s.strip()]

    # Pre-normalize all drugs once
    drug_info_map = {}
    for drug in drugs:
        drug_info_map[drug] = detect_drug_info_with_llm(drug)

    for supplement in supplements:
        for drug in drugs:
            drug_info = drug_info_map[drug]

            normalized_drug = drug_info.get("normalized_drug_name", drug)
            brand_name = drug_info.get("brand_name", "Not available")
            detected_drug_class = drug_info.get("drug_class", "Not available")
            therapeutic_category = drug_info.get("therapeutic_category", "Not available")

            matched_doc = find_best_interaction_for_pair(
                docs=docs,
                supplement_name=supplement,
                user_drug_name=drug,
                normalized_drug=normalized_drug,
                detected_drug_class=detected_drug_class,
                brand_name=brand_name
            )

            if matched_doc:
                interactions.append(
                    format_interaction_result(
                        matched_doc=matched_doc,
                        supplement_name=supplement,
                        user_drug_name=drug,
                        normalized_drug=normalized_drug,
                        detected_drug_class=detected_drug_class,
                        therapeutic_category=therapeutic_category
                    )
                )
            else:
                no_interactions.append({
                    "supplement": supplement,
                    "drug": drug,
                    "status": "not_found"
                })

    return {
        "status": "success",
        "input_drugs": drugs,
        "input_supplements": supplements,
        "total_pairs_checked": len(drugs) * len(supplements),
        "total_interactions_found": len(interactions),
        "interactions": interactions,
        "no_interactions": no_interactions
    }


# =========================
# LOAD DATA ONCE
# =========================
file_path = os.path.join(os.path.dirname(__file__), "herb_interactions.txt")
docs = parse_herb_text_file(file_path)

print(f"[INFO] Loaded {len(docs)} herb-drug interaction documents")


# =========================
# API ROUTE FOR REGISTRATION
# =========================
@app.route("/api/registration-interactions", methods=["POST"])
def registration_interactions():
    try:
        data = request.get_json(force=True)

        drugs = data.get("drugs", [])
        supplements = data.get("supplements", [])

        if not isinstance(drugs, list) or not isinstance(supplements, list):
            return jsonify({
                "status": "error",
                "message": "drugs and supplements must be arrays"
            }), 400

        result = check_registration_interactions(
            docs=docs,
            drugs=drugs,
            supplements=supplements
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/test-registration", methods=["POST"])
def test_registration():
    try:
        data = request.get_json(force=True)
        drugs = data.get("drugs", [])
        supplements = data.get("supplements", [])

        if not drugs and not supplements:
            return jsonify({"status": "error", "message": "No drugs or supplements provided"}), 400

        result = check_registration_interactions(
            docs=docs,
            drugs=drugs,
            supplements=supplements
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)