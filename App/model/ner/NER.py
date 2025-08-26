import os
import json
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

# --- Define model paths relative to this script's location ---
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "model.onnx")

# --- Load tokenizer and model configuration ---
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
with open(os.path.join(MODEL_DIR, "config.json"), "r", encoding="utf-8") as f:
    cfg = json.load(f)
id2label = {int(k): v for k, v in cfg.get("id2label", {}).items()}

# --- Define the specific medical entity types to extract ---
# These IDs correspond to labels like 'B-Disease_disorder', 'B-Medication', etc.
desired_tag_names = {id2label[i][2:] for i in [12, 13, 23, 37, 40, 55, 56, 66, 77, 80] if i in id2label}

# --- Initialize ONNX Runtime session ---
try:
    session = ort.InferenceSession(
        MODEL_PATH,
        providers=["CPUExecutionProvider"],
    )
except Exception as e:
    session = ort.InferenceSession(
        MODEL_PATH,
        providers=["QNNExecutionProvider"],
    )

# --- Main function to process a sentence ---
def extract_medical_terms(sentence: str):
    # --- Extracts medical terms from a given sentence using the loaded ONNX model ---
    
    # --- 1. Tokenize and prepare input for the ONNX model ---
    enc = tokenizer(
        sentence,
        return_tensors="np",
        truncation=True,
        max_length=128,
        padding='max_length'
    )
    onnx_inputs = {}
    enc_np = {k: (v.astype(np.int64) if k in ['input_ids', 'attention_mask'] else v) for k, v in enc.items()}
    for inp in session.get_inputs():
        name = inp.name
        base = name.split(":")[0]
        if base in enc_np:
            onnx_inputs[name] = enc_np[base]

    # --- 2. Run inference ---
    outputs = session.run(None, onnx_inputs)
    logits = outputs[0]
    pred_ids = logits.argmax(-1)[0].tolist()
    labels_token = [id2label.get(i, "O") for i in pred_ids]

    # --- 3. Post-process the output to reconstruct entities ---
    tokens = tokenizer.tokenize(sentence)
    tagged_words = list(zip(tokens, labels_token[1:len(tokens)+1]))

    extracted_words_list = []
    current_entity_tokens = []
    current_tag_name = None

    # --- Iterate through tokens and their predicted BIO labels ---
    for token, label in tagged_words:
        tag_name = label[2:] if label.startswith(('B-', 'I-')) else label
        
        # --- If the token continues the current entity ---
        if tag_name == current_tag_name and tag_name != 'O':
            current_entity_tokens.append(token.replace('##', ''))
        else:
            # --- If a previous entity has just ended, save it ---
            if current_entity_tokens and current_tag_name in desired_tag_names:
                extracted_words_list.append("".join(current_entity_tokens))
            
            # --- If a new desired entity starts ---
            if tag_name in desired_tag_names:
                current_entity_tokens = [token.replace('##', '')]
                current_tag_name = tag_name
            else:
                # --- Reset if the token is 'O' or not a desired entity ---
                current_entity_tokens = []
                current_tag_name = None

    # --- Add the last entity if the sentence ends with one ---
    if current_entity_tokens and current_tag_name in desired_tag_names:
        extracted_words_list.append("".join(current_entity_tokens))

    return extracted_words_list

# --- Test block to run when the script is executed directly ---
if __name__ == "__main__":
    sentence = "A 65-year-old male presented with persistent cough and shortness of breath; a chest X-ray revealed signs consistent with chronic obstructive pulmonary disease."
    terms = extract_medical_terms(sentence)
    print(f"Extracted terms: {terms}")
