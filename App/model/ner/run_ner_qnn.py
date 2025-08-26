import re
import json
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

# --- 0. Input text for testing ---
doctor = ("The patient presented with persistent dyspnea and chest discomfort, "
          "leading to a clinical diagnosis of community-acquired pneumonia "
          "confirmed by chest X-ray showing right lower lobe consolidation.")

# --- 1. Model path configuration ---
MODEL_DIR = r"C:\Users\Qualcomm\clinical_ner_onnx"
MODEL_PATH = f"{MODEL_DIR}\\model.onnx"

# --- 2. Load tokenizer and label mappings from config ---
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, use_fast=True)
with open(f"{MODEL_DIR}\\config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)
id2label = {int(k): v for k, v in cfg.get("id2label", {}).items()}

# --- 3. Set up ONNX session with QNNExecutionProvider (for NPU) ---
sess_opts = ort.SessionOptions()
# --- Disable CPU fallback to ensure it runs on the NPU if configured ---
sess_opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")

provider_options = [{"backend_path": "QnnHtp.dll", "enable_htp_fp16_precision": "1"}]
session = ort.InferenceSession(
    MODEL_PATH,
    sess_options=sess_opts,
    providers=["QNNExecutionProvider"],
    provider_options=provider_options,
)
print("Available EPs:", ort.get_available_providers())
print("Session uses EPs:", session.get_providers())

# --- 4. Preprocess text and prepare inputs for the model ---
enc = tokenizer(
    doctor,
    return_tensors="np",
    truncation=True,
    max_length=512,
    return_offsets_mapping=True, # Get character offsets for each token
)

# --- Map tokenizer outputs to the expected ONNX input names ---
onnx_inputs = {}
enc_np = {k: (v if isinstance(v, np.ndarray) else np.array(v)) for k, v in enc.items()}
for inp in session.get_inputs():
    name = inp.name
    base = name.split(":")[0]
    if base in enc_np:
        onnx_inputs[name] = enc_np[base]

# --- 5. Run inference ---
outputs = session.run(None, onnx_inputs)
logits = outputs[0]
pred_ids = logits.argmax(-1)[0].tolist()

# --- Convert predicted IDs back to BIO labels (e.g., "B-Disease_disorder") ---
labels_token = [id2label.get(i, "O") for i in pred_ids]

# --- 6. Post-process to convert BIO labels and offsets into entity spans ---
offsets = enc["offset_mapping"][0]

def bio_to_spans(labels, offsets, text):
    # --- Converts a sequence of BIO labels into a list of entities with text and offsets ---
    spans = []
    start = end = None
    ent_type = None
    for lab, ofs in zip(labels, offsets):
        s, e = int(ofs[0]), int(ofs[1])
        if e == 0 and s == 0: # Ignore special tokens like [CLS], [SEP]
            continue

        if lab.startswith("B-"): # Beginning of a new entity
            if start is not None: # Save the previous entity first
                spans.append({"label": ent_type, "start": start, "end": end, "text": text[start:end]})
            start, end, ent_type = s, e, lab[2:]
        elif lab.startswith("I-") and ent_type == lab[2:] and start is not None: # Inside an entity
            end = e
        else: # Outside of an entity ('O' tag)
            if start is not None: # Save the completed entity
                spans.append({"label": ent_type, "start": start, "end": end, "text": text[start:end]})
            start = end = ent_type = None
    if start is not None: # Save the last entity if the text ends with one
        spans.append({"label": ent_type, "start": start, "end": end, "text": text[start:end]})
    return spans

spans = bio_to_spans(labels_token, offsets, doctor)

# --- 7. Define allowed entity types and a normalization function ---
allowed_base_labels = {
    "Diagnostic_procedure",
    "Disease_disorder",
    "Medication",
    "Sign_symptom",
    "Therapeutic_procedure",
}
def normalize_base(label_base: str) -> str:
    # --- Corrects potential typos in model output labels ---
    fixes = {"Disease_discorder": "Disease_disorder"}
    return fixes.get(label_base, label_base)

# --- 8. Extract and filter words from the identified spans ---
word_re = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-]*")
words = []
for s in spans:
    base = normalize_base(s["label"])
    if base in allowed_base_labels:
        # --- Find all individual words within the entity text ---
        words.extend(word_re.findall(s["text"]))

# --- Get a unique, sorted list of the final words ---
words = sorted(set(words), key=str.lower)

print("\n=== Filtered Words (by allowed labels) ===")
print(words)

# --- For debugging: show all unique entity types found in the text ---
found = sorted(set(normalize_base(s["label"]) for s in spans))
print("\nFound label bases:", found)
