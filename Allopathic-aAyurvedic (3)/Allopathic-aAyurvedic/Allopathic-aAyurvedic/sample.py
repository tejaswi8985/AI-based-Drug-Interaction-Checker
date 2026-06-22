from flask import Flask, request, jsonify
from flask_cors import CORS 

app = Flask(__name__)
CORS(app)  

@app.route("/api")
def api():
    try:
        question = request.args.get("q", "").lower()

        data = {

            "warfarin": {
                "allopathic_drug_name": "Anticoagulant / Antiplatelet drugs",
                "ayurvedic_name": "Amalaki",
                "brand_names": "none",
                "canonical_name": "Amalaki",
                "clinical_effect": "Increased risk of bruising and bleeding.",
                "detected_drug_class": "Vitamin K antagonist",
                "drug_class": "Blood Thinners",
                "drug_type": "Drug Class",
                "evidence_text": "Indian gooseberry might slow blood clotting.",
                "interaction_severity": "danger",
                "mechanism": "Indian gooseberry may slow blood clotting.",
                "normalized_drug_name": "warfarin",
                "recommendation": "Use cautiously and monitor for bleeding.",
                "source": "metadata_match",
                "status": "found",
                "therapeutic_category": "Anticoagulant",
                "user_entered_drug": question
            },

            "aspirin": {
                "allopathic_drug_name": "NSAID",
                "ayurvedic_name": "Ginkgo Biloba",
                "brand_names": "none",
                "canonical_name": "Ginkgo",
                "clinical_effect": "Increased bleeding risk.",
                "detected_drug_class": "Antiplatelet",
                "drug_class": "Pain Reliever",
                "drug_type": "Drug",
                "evidence_text": "Ginkgo may enhance antiplatelet effects.",
                "interaction_severity": "danger",
                "mechanism": "Inhibits platelet aggregation.",
                "normalized_drug_name": "aspirin",
                "recommendation": "Avoid combination unless monitored.",
                "source": "metadata_match",
                "status": "found",
                "therapeutic_category": "Analgesic",
                "user_entered_drug": question
            },

            "metformin": {
                "allopathic_drug_name": "Antidiabetic",
                "ayurvedic_name": "Fenugreek",
                "brand_names": "none",
                "canonical_name": "Methi",
                "clinical_effect": "Low blood sugar (hypoglycemia).",
                "detected_drug_class": "Biguanide",
                "drug_class": "Diabetes",
                "drug_type": "Drug",
                "evidence_text": "Fenugreek lowers blood glucose levels.",
                "interaction_severity": "moderate",
                "mechanism": "Enhances insulin sensitivity.",
                "normalized_drug_name": "metformin",
                "recommendation": "Monitor glucose levels.",
                "source": "metadata_match",
                "status": "found",
                "therapeutic_category": "Antidiabetic",
                "user_entered_drug": question
            },

            "lisinopril": {
                "allopathic_drug_name": "ACE Inhibitor",
                "ayurvedic_name": "Licorice",
                "brand_names": "none",
                "canonical_name": "Yashtimadhu",
                "clinical_effect": "Reduced drug effectiveness.",
                "detected_drug_class": "Antihypertensive",
                "drug_class": "Blood Pressure",
                "drug_type": "Drug",
                "evidence_text": "Licorice may increase blood pressure.",
                "interaction_severity": "moderate",
                "mechanism": "Causes sodium retention.",
                "normalized_drug_name": "lisinopril",
                "recommendation": "Avoid long-term use together.",
                "source": "metadata_match",
                "status": "found",
                "therapeutic_category": "Antihypertensive",
                "user_entered_drug": question
            },

            "atorvastatin": {
                "allopathic_drug_name": "Statin",
                "ayurvedic_name": "Garlic",
                "brand_names": "none",
                "canonical_name": "Lahsun",
                "clinical_effect": "Increased side effects.",
                "detected_drug_class": "Lipid-lowering",
                "drug_class": "Cholesterol",
                "drug_type": "Drug",
                "evidence_text": "Garlic may enhance statin effects.",
                "interaction_severity": "moderate",
                "mechanism": "Alters liver metabolism.",
                "normalized_drug_name": "atorvastatin",
                "recommendation": "Monitor liver function.",
                "source": "metadata_match",
                "status": "found",
                "therapeutic_category": "Lipid-lowering",
                "user_entered_drug": question
            },

            "ibuprofen": {
                "allopathic_drug_name": "NSAID",
                "ayurvedic_name": "Turmeric",
                "brand_names": "none",
                "canonical_name": "Haldi",
                "clinical_effect": "Increased bleeding risk.",
                "detected_drug_class": "Pain Reliever",
                "drug_class": "NSAID",
                "drug_type": "Drug",
                "evidence_text": "Turmeric has anticoagulant effects.",
                "interaction_severity": "moderate",
                "mechanism": "Inhibits clotting pathways.",
                "normalized_drug_name": "ibuprofen",
                "recommendation": "Use cautiously.",
                "source": "metadata_match",
                "status": "found",
                "therapeutic_category": "Analgesic",
                "user_entered_drug": question
            },

            "paracetamol": {
                "allopathic_drug_name": "Analgesic",
                "ayurvedic_name": "Aloe Vera",
                "brand_names": "none",
                "canonical_name": "Kumari",
                "clinical_effect": "Liver toxicity risk.",
                "detected_drug_class": "Pain Reliever",
                "drug_class": "Analgesic",
                "drug_type": "Drug",
                "evidence_text": "Aloe may affect liver enzymes.",
                "interaction_severity": "moderate",
                "mechanism": "Alters hepatic metabolism.",
                "normalized_drug_name": "paracetamol",
                "recommendation": "Limit combined usage.",
                "source": "metadata_match",
                "status": "found",
                "therapeutic_category": "Pain Relief",
                "user_entered_drug": question
            },

            "amoxicillin": {
                "allopathic_drug_name": "Antibiotic",
                "ayurvedic_name": "Neem",
                "brand_names": "none",
                "canonical_name": "Neem",
                "clinical_effect": "Reduced antibiotic effect.",
                "detected_drug_class": "Penicillin",
                "drug_class": "Antibiotic",
                "drug_type": "Drug",
                "evidence_text": "Neem has antimicrobial properties.",
                "interaction_severity": "low",
                "mechanism": "May interfere with gut flora.",
                "normalized_drug_name": "amoxicillin",
                "recommendation": "Use separately.",
                "source": "metadata_match",
                "status": "found",
                "therapeutic_category": "Antibiotic",
                "user_entered_drug": question
            },

            "insulin": {
                "allopathic_drug_name": "Hormone",
                "ayurvedic_name": "Bitter Melon",
                "brand_names": "none",
                "canonical_name": "Karela",
                "clinical_effect": "Hypoglycemia risk.",
                "detected_drug_class": "Antidiabetic",
                "drug_class": "Diabetes",
                "drug_type": "Drug",
                "evidence_text": "Bitter melon lowers blood sugar.",
                "interaction_severity": "danger",
                "mechanism": "Enhances glucose uptake.",
                "normalized_drug_name": "insulin",
                "recommendation": "Monitor sugar closely.",
                "source": "metadata_match",
                "status": "found",
                "therapeutic_category": "Antidiabetic",
                "user_entered_drug": question
            },

            "clopidogrel": {
                "allopathic_drug_name": "Antiplatelet",
                "ayurvedic_name": "Ginger",
                "brand_names": "none",
                "canonical_name": "Adrak",
                "clinical_effect": "Increased bleeding risk.",
                "detected_drug_class": "Blood Thinner",
                "drug_class": "Cardiac",
                "drug_type": "Drug",
                "evidence_text": "Ginger affects platelet aggregation.",
                "interaction_severity": "danger",
                "mechanism": "Enhances anticoagulant effect.",
                "normalized_drug_name": "clopidogrel",
                "recommendation": "Avoid high doses.",
                "source": "metadata_match",
                "status": "found",
                "therapeutic_category": "Antiplatelet",
                "user_entered_drug": question
            }

        }

        answer = data.get(question, {
            "status": "not found",
            "user_entered_drug": question
        })

        return jsonify(answer), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")