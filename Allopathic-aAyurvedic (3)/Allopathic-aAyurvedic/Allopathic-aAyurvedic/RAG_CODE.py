import os
import re
import json
from typing import List, Dict, Optional

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Allow requests from your Vite frontend
CORS(app, resources={r"/api*": {"origins": "*"}})

# =========================
# LOAD ENV + INIT MODELS
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

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=API_KEY
)


# =========================
# HELPERS
# =========================
def normalize_text(s: str) -> str:
    """
    Normalize text for matching:
    - lowercase
    - remove punctuation
    - collapse whitespace
    """
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s,/+\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def split_csv_like(value: str) -> List[str]:
    """
    Split comma-separated values into normalized tokens.
    """
    if not value:
        return []
    return [normalize_text(x.strip()) for x in value.split(",") if x.strip()]


def safe_json_parse(content: str) -> Dict:
    """
    Safely parse JSON from LLM output.
    Removes code fences and tries to extract JSON object.
    """
    if not content:
        return {}

    content = content.strip()

    # Remove markdown fences if present
    content = re.sub(r"^```json\s*|\s*```$", "", content, flags=re.IGNORECASE | re.DOTALL).strip()

    # Try direct parse
    try:
        return json.loads(content)
    except Exception:
        pass

    # Try extracting JSON object from mixed text
    try:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass

    return {}


def extract_field(text: str, field_name: str) -> str:
    """
    Extracts single-line field values like:
    Primary Name: Amalaki
    Drug: Anticoagulant / Antiplatelet drugs
    """
    pattern = rf"^{re.escape(field_name)}\s*:\s*(.*)$"
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_value_from_doc(text: str, field_name: str) -> str:
    """
    Extract field from final retrieved document text.
    Example:
    Herb: Ajamoda
    """
    pattern = rf"^{re.escape(field_name)}\s*:\s*(.*)$"
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else "Not available"


def token_match(query: str, target: str) -> bool:
    """
    Stronger token-aware matching:
    - exact full normalized match
    - token present in comma-separated / slash-separated lists
    - substring fallback
    """
    q = normalize_text(query)
    t = normalize_text(target)

    if not q or not t:
        return False

    if q == t:
        return True

    # Tokenize target by comma, slash, semicolon
    target_parts = re.split(r"[,/;|]", t)
    target_parts = [x.strip() for x in target_parts if x.strip()]

    if q in target_parts:
        return True

    # Also compare target words
    target_words = set(t.split())
    if q in target_words:
        return True

    # fallback
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
    """
    Build ranked query variants for drug matching.
    Priority:
    1. normalized generic
    2. user-entered
    3. brand
    4. aliases from dictionary
    5. detected class
    """
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
    """
    Parse herb_interactions.txt where herb sections look like:

    3)
    Primary Name: Amalaki
    ...
    Interaction 1
    Severity: Moderate
    ...

    Creates ONE Document per interaction.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    # Split by herb block number like:
    # 1)
    # 2)
    # 3)
    herb_blocks = re.split(r"(?=^\s*\d+\)\s*$)", text, flags=re.MULTILINE)

    documents = []

    for idx, block in enumerate(herb_blocks):
        if not block.strip():
            continue

        # Must contain a primary name
        if not re.search(r"^\s*Primary Name\s*:", block, re.IGNORECASE | re.MULTILINE):
            continue

        primary_name = extract_field(block, "Primary Name")
        canonical_name = extract_field(block, "Canonical Name")
        system = extract_field(block, "System")
        indian_names = extract_field(block, "Indian/Common Names")
        english_names = extract_field(block, "English Names")
        botanical_names = extract_field(block, "Botanical Names")
        aliases = extract_field(block, "Normalized Search Aliases")

        print(f"[DEBUG] Parsing herb block #{idx+1}: {primary_name}")

        # Split interaction blocks
        interaction_blocks = re.split(
            r"(?=^\s*Interaction\s+\d+\s*$)",
            block,
            flags=re.IGNORECASE | re.MULTILINE
        )

        herb_doc_count = 0

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

            # Skip empty/broken interaction blocks
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
            herb_doc_count += 1

        if herb_doc_count == 0:
            print(f"[WARN] No interaction records found for herb: {primary_name}")
        else:
            print(f"[DEBUG] Added {herb_doc_count} interaction docs for herb: {primary_name}")

    return documents


# =========================
# BUILD RETRIEVER
# =========================
def build_retriever_from_herb_txt(file_path: str):
    docs = parse_herb_text_file(file_path)

    print(f"[INFO] Built {len(docs)} interaction docs")

    if not docs:
        raise ValueError("No documents loaded from the herb interactions file.")

    unique_herbs = sorted(set(doc.metadata.get("primary_name", "") for doc in docs))
    print(f"[DEBUG] Unique herbs parsed: {len(unique_herbs)}")
    print("[DEBUG] First 30 herbs:")
    for herb in unique_herbs[:30]:
        print(" -", herb)

    amalaki_docs = [d for d in docs if normalize_text(d.metadata.get("primary_name", "")) == "amalaki"]
    print(f"[DEBUG] Amalaki docs found: {len(amalaki_docs)}")

    vectorstore = FAISS.from_documents(docs, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    return retriever, docs


# =========================
# LLM: EXTRACT HERB + DRUG
# =========================
def extract_herb_and_drug_with_llm(question: str) -> dict:
    prompt = ChatPromptTemplate.from_template("""
You are an information extraction assistant for herb-drug interaction questions.

Extract:
1. Ayurvedic herb name
2. Allopathic drug name

Return ONLY valid JSON in this exact format:
{{
  "herb_name": "<herb name>",
  "drug_name": "<drug name>"
}}

Rules:
- Extract the likely herb and drug from the question.
- The herb may appear before or after the drug.
- Handle spelling mistakes if possible.
- If missing, return "Not available".
- Do not explain.
- Do not use markdown.
- Do not return code fences.

Question:
{question}
""")

    chain = prompt | llm
    response = chain.invoke({"question": question})

    parsed = safe_json_parse(response.content)

    if not parsed:
        return {
            "herb_name": "Not available",
            "drug_name": "Not available"
        }

    return {
        "herb_name": parsed.get("herb_name", "Not available"),
        "drug_name": parsed.get("drug_name", "Not available")
    }


# =========================
# LLM: NORMALIZE DRUG + DETECT CLASS
# =========================
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
# MATCHING LOGIC (BEST MATCH ONLY)
# =========================
def score_herb_match(herb_name: str, doc: Document) -> int:
    """
    Higher score = better herb match
    """
    herb_q = normalize_text(herb_name)

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


def score_drug_match(
    user_drug_name: str,
    normalized_drug: str,
    detected_drug_class: str,
    brand_name: str,
    doc: Document
) -> int:
    """
    Higher score = better drug match.
    STRICT priority:
    1. exact normalized generic drug
    2. exact user-entered drug
    3. brand match
    4. alias match
    5. class match
    """
    doc_drug = doc.metadata.get("drug", "")
    doc_brand = doc.metadata.get("brand_names", "")
    doc_class = doc.metadata.get("drug_class", "")

    # 1) exact normalized generic vs stored drug
    if normalized_drug and normalized_drug != "Not available" and token_match(normalized_drug, doc_drug):
        return 100

    # 2) user input vs stored drug
    if user_drug_name and user_drug_name != "Not available" and token_match(user_drug_name, doc_drug):
        return 95

    # 3) brand name match
    if brand_name and brand_name != "Not available":
        if token_match(brand_name, doc_brand):
            return 90
        if token_match(brand_name, doc_drug):
            return 88

    # 4) alias match from dictionary
    variants = build_drug_query_variants(user_drug_name, normalized_drug, detected_drug_class, brand_name)
    for v in variants:
        if token_match(v, doc_drug):
            return 85
        if token_match(v, doc_brand):
            return 80

    # 5) class match (lowest priority)
    if detected_drug_class and detected_drug_class != "Not available" and token_match(detected_drug_class, doc_class):
        return 60

    return 0


def find_best_exact_or_fuzzy_match(
    docs: List[Document],
    herb_name: str,
    user_drug_name: str,
    normalized_drug: str,
    detected_drug_class: str,
    brand_name: str
) -> Optional[Document]:
    """
    Return ONLY the single best matching document.
    If an exact drug match exists, it will beat class-level matches.
    """
    candidates = []

    for doc in docs:
        herb_score = score_herb_match(herb_name, doc)
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

        candidates.append((total_score, herb_score, drug_score, doc))

        print(
            f"[DEBUG] Candidate -> Herb: {doc.metadata.get('primary_name')} | "
            f"Drug: {doc.metadata.get('drug')} | "
            f"Herb Score: {herb_score} | Drug Score: {drug_score} | Total: {total_score}"
        )

    if not candidates:
        return None

    # Sort highest total first, then higher drug score first
    candidates.sort(key=lambda x: (x[0], x[2], x[1]), reverse=True)

    best_doc = candidates[0][3]
    return best_doc


def find_best_match_in_retrieved_docs(
    retrieved_docs: List[Document],
    herb_name: str,
    user_drug_name: str,
    normalized_drug: str,
    detected_drug_class: str,
    brand_name: str
) -> Optional[Document]:
    """
    Among retrieved FAISS docs, return ONLY the single best match.
    """
    best_doc = None
    best_score = -1
    best_drug_score = -1

    for doc in retrieved_docs:
        text = doc.page_content

        top_herb = extract_value_from_doc(text, "Herb")
        top_canonical = extract_value_from_doc(text, "Canonical Name")
        top_drug = extract_value_from_doc(text, "Interaction Drug")
        top_brand = extract_value_from_doc(text, "Brand Names")
        top_class = extract_value_from_doc(text, "Drug Class")

        # Herb score
        herb_score = 0
        if token_match(herb_name, top_herb):
            herb_score = 100
        elif token_match(herb_name, top_canonical):
            herb_score = 90

        if herb_score == 0:
            continue

        # Drug score
        drug_score = 0
        if normalized_drug and token_match(normalized_drug, top_drug):
            drug_score = 100
        elif user_drug_name and token_match(user_drug_name, top_drug):
            drug_score = 95
        elif brand_name and token_match(brand_name, top_brand):
            drug_score = 90
        else:
            variants = build_drug_query_variants(user_drug_name, normalized_drug, detected_drug_class, brand_name)
            alias_hit = False
            for v in variants:
                if token_match(v, top_drug):
                    drug_score = 85
                    alias_hit = True
                    break
                if token_match(v, top_brand):
                    drug_score = 80
                    alias_hit = True
                    break

            if not alias_hit and detected_drug_class and token_match(detected_drug_class, top_class):
                drug_score = 60

        if drug_score == 0:
            continue

        total_score = herb_score + drug_score

        print(
            f"[DEBUG] FAISS Candidate -> Herb: {top_herb} | Drug: {top_drug} | "
            f"Herb Score: {herb_score} | Drug Score: {drug_score} | Total: {total_score}"
        )

        # tie-break: prefer higher drug specificity
        if total_score > best_score or (total_score == best_score and drug_score > best_drug_score):
            best_score = total_score
            best_drug_score = drug_score
            best_doc = doc

    return best_doc


# =========================
# FINAL STRUCTURED ANSWER
# =========================
def format_answer(
    matched_doc: Document,
    user_drug_name: str,
    normalized_drug: str,
    detected_drug_class: str,
    therapeutic_category: str
) -> Dict:
    text = matched_doc.page_content

    return {
        "status": "found",
        "ayurvedic_name": extract_value_from_doc(text, "Herb"),
        "canonical_name": extract_value_from_doc(text, "Canonical Name"),
        "user_entered_drug": user_drug_name,
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
        "evidence_text": extract_value_from_doc(text, "Evidence Text"),
        "source": "metadata_or_faiss_match"
    }


from typing import Dict

def answer_herb_drug_question(retriever, docs, question: str) -> Dict:
    # Step 1: extract herb + user drug
    parsed = extract_herb_and_drug_with_llm(question)

    herb_name = parsed.get("herb_name", "Not available")
    user_drug_name = parsed.get("drug_name", "Not available")

    print(f"[DEBUG] Extracted herb: {herb_name}")
    print(f"[DEBUG] User-entered drug: {user_drug_name}")

    if herb_name == "Not available" or user_drug_name == "Not available":
        return {
            "status": "not_found",
            "message": "The interaction is not available in the knowledge base. Please contact healthcare provider."
        }

    # Step 2: normalize drug + detect class
    drug_info = detect_drug_info_with_llm(user_drug_name)

    normalized_drug = drug_info.get("normalized_drug_name", user_drug_name)
    detected_brand_name = drug_info.get("brand_name", "Not available")
    detected_drug_class = drug_info.get("drug_class", "Not available")
    therapeutic_category = drug_info.get("therapeutic_category", "Not available")

    print(f"[DEBUG] Normalized drug: {normalized_drug}")
    print(f"[DEBUG] Detected brand: {detected_brand_name}")
    print(f"[DEBUG] Detected drug class: {detected_drug_class}")
    print(f"[DEBUG] Therapeutic category: {therapeutic_category}")

    # =====================================================
    # STEP 3: Exact/fuzzy metadata lookup FIRST (BEST ONE ONLY)
    # =====================================================
    matched_doc = find_best_exact_or_fuzzy_match(
        docs=docs,
        herb_name=herb_name,
        user_drug_name=user_drug_name,
        normalized_drug=normalized_drug,
        detected_drug_class=detected_drug_class,
        brand_name=detected_brand_name
    )

    if matched_doc:
        print("[DEBUG] Found match via metadata filtering.")
        result = format_answer(
            matched_doc=matched_doc,
            user_drug_name=user_drug_name,
            normalized_drug=normalized_drug,
            detected_drug_class=detected_drug_class,
            therapeutic_category=therapeutic_category
        )
        result["source"] = "metadata_match"
        return result

    # =====================================================
    # STEP 4: FAISS fallback
    # =====================================================
    search_query = f"""
Herb: {herb_name}
Drug: {user_drug_name}
Normalized Drug: {normalized_drug}
Brand Name: {detected_brand_name}
Drug Class: {detected_drug_class}
Therapeutic Category: {therapeutic_category}
"""

    print("[DEBUG] No metadata match found. Falling back to FAISS retrieval...")
    retrieved_docs = retriever.invoke(search_query)

    if not retrieved_docs:
        return {
            "status": "not_found",
            "message": "The interaction is not available in the knowledge base. Please contact healthcare provider."
        }

    print(f"[DEBUG] Retrieved {len(retrieved_docs)} docs from FAISS")

    for i, doc in enumerate(retrieved_docs, start=1):
        print(f"\n[DEBUG] Retrieved doc #{i}")
        print(doc.page_content[:500])

    matched_doc = find_best_match_in_retrieved_docs(
        retrieved_docs=retrieved_docs,
        herb_name=herb_name,
        user_drug_name=user_drug_name,
        normalized_drug=normalized_drug,
        detected_drug_class=detected_drug_class,
        brand_name=detected_brand_name
    )

    if not matched_doc:
        return {
            "status": "not_found",
            "message": "The interaction is not available in the knowledge base. Please contact healthcare provider."
        }

    print("[DEBUG] Found match via FAISS fallback.")

    # =====================================================
    # STEP 5: final structured output
    # =====================================================
    result = format_answer(
        matched_doc=matched_doc,
        user_drug_name=user_drug_name,
        normalized_drug=normalized_drug,
        detected_drug_class=detected_drug_class,
        therapeutic_category=therapeutic_category
    )
    result["source"] = "faiss_match"
    return result

# =========================
# MAIN
# =========================


file_path = "C:\\Users\\shado\\Downloads\\Allopathic-aAyurvedic\\Allopathic-aAyurvedic\\herb_interactions.txt"   # keep txt file in same folder
retriever, docs = build_retriever_from_herb_txt(file_path)
@app.route("/")
def index():
    try:
        answer = answer_herb_drug_question(retriever, docs, "can i take amalaki with warfarin?")
        print("\n" + json.dumps(answer, indent=2, ensure_ascii=False))
    except Exception as e:
        print("\n" + json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2, ensure_ascii=False))
    return render_template("index.html")

@app.route("/api")
def api():
    try:
        question = request.args.get("q")
        answer = answer_herb_drug_question(retriever, docs, question)
        print(answer)
        # answer = {
        #   "allopathic_drug_name": "Anticoagulant / Antiplatelet drugs",
        #   "ayurvedic_name": "Amalaki",
        #   "brand_names": "none",
        #   "canonical_name": "Amalaki",
        #   "clinical_effect": "Increased risk of bruising and bleeding.",
        #   "detected_drug_class": "Vitamin K antagonist",
        #   "drug_class": "Blood Thinners",
        #   "drug_type": "Drug Class",
        #   "evidence_text": "Indian gooseberry might slow blood clotting. Taking Indian gooseberry along with medications that also slow blood clotting might increase the risk of bruising and bleeding.",
        #   "interaction_severity": "Moderate",
        #   "mechanism": "Indian gooseberry may slow blood clotting.",
        #   "normalized_drug_name": "warfarin",
        #   "recommendation": "Use cautiously and monitor for signs of bleeding.",
        #   "source": "metadata_match",
        #   "status": "found",
        #   "therapeutic_category": "Anticoagulant",
        #   "user_entered_drug": "warfarin"
        # }
        return jsonify(answer), 200
    except Exception as e:
        print("\n" + json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2, ensure_ascii=False))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)