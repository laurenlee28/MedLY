# --- PDF generation imports ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.lib import colors

# --- Core application imports ---
import os
import json
import asyncio
import datetime
import subprocess
import sys
import time
import threading
from contextlib import asynccontextmanager

# --- FastAPI and related imports ---
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# --- Image processing and OCR imports ---
import pyautogui
import pytesseract
import cv2
import numpy as np
from uvicorn import run

# --- Application state for Electron communication ---
app_state = {"models_loaded": False}

# --- Model loading logic ---
try:
    from model.ner.NER import extract_medical_terms
except ImportError:
    print("WARNING: NER model could not be imported. Using a placeholder function.")
    def extract_medical_terms(text):
        return [word for word in text.split() if len(word) > 5]

def initialize_all_models():
    # --- Place all heavy model initialization code here ---
    print("Initializing actual models...")
    # Example: Load NER, Qwen, or other models from disk.
    # This is where the time-consuming ONNX model loading should happen.
    time.sleep(10) # Simulating a 10-second model load time.
    print("Actual model initialization complete.")


def load_all_models_in_background():
    # --- Wrapper function to run in a background thread ---
    print("Starting model loading in the background...")
    try:
        initialize_all_models()
        app_state["models_loaded"] = True
        print("All models loaded successfully!")
    except Exception as e:
        print(f"Critical error during model loading: {e}")
        app_state["models_loaded"] = False

# --- FastAPI lifespan manager for startup/shutdown events ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Code to run on application startup ---
    print("FastAPI Lifespan: Startup event triggered.")
    # --- Start model loading in a separate thread to not block the server ---
    thread = threading.Thread(target=load_all_models_in_background)
    thread.start()
    yield
    # --- Code to run on application shutdown ---
    print("FastAPI Lifespan: Shutdown event triggered.")

# --- Initialize FastAPI app with the lifespan manager ---
app = FastAPI(lifespan=lifespan)


# --- Basic configuration and path settings ---
def get_app_path():
    # --- Get the correct root path for both dev and packaged app ---
    return os.path.dirname(os.path.abspath(__file__))

ROOT_DIR = get_app_path()
STATIC_DIR = os.path.join(ROOT_DIR, "static")
QWEN_SCRIPT = os.path.join(ROOT_DIR, "model", "phi", "genie_bundle", "run_qwen.py")
INDEX_HTML = os.path.join(STATIC_DIR, "index.html")

# --- Create directories for temporary files and debug captures ---
DEBUG_DIR = os.path.join(ROOT_DIR, "debug_captures")
if not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)

TEMP_DIR = os.path.join(ROOT_DIR, "temp")
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# --- Middleware and static file configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/temp", StaticFiles(directory=TEMP_DIR), name="temp")

# --- Tesseract OCR engine path configuration ---
TESSERACT_PATH = os.path.join(ROOT_DIR, "Tesseract-OCR", "tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# --- Global variables for the transcription pipeline ---
REGION_LEFT = 0; REGION_TOP = 0; REGION_WIDTH = 2700; REGION_HEIGHT = 120
conversations_db = []
unique_terms = set()
full_transcript_store = ""

# --- Core functional components ---
def capture_and_ocr(region):
    # --- Captures a screen region, preprocesses, and performs OCR ---
    try:
        screenshot = pyautogui.screenshot(region=region)
        screenshot_np = np.array(screenshot)
        gray_image = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)
        # --- Thresholding for better text recognition on dark backgrounds ---
        _, binary_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY)
        custom_config = r'--oem 3 --psm 7' # PSM 7 assumes a single line of text
        text = pytesseract.image_to_string(binary_image, lang='kor+eng', config=custom_config)
        return text.strip()
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

def run_llm(prompt: str):
    # --- Runs the external LLM script as a subprocess ---
    if not prompt: return ""
    print("-" * 50); print(f"Prompt sent to LLM: {prompt}"); print("-" * 50)
    try:
        python_executable = sys.executable
        cmd = [python_executable, QWEN_SCRIPT, "--text", prompt]
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=ROOT_DIR,
            encoding='utf-8', errors='replace', check=False
        )
        if result.stderr:
            return f"An error has occurred while processing LLM: {result.stderr.strip()}"
        return result.stdout.strip()
    except Exception as e:
        return f"An error has occurred while processing LLM: {e!r}"

async def process_llm_and_save(websocket: WebSocket, text: str):
    # --- Generates a summary, saves it, and sends it to the client ---
    prompt = f"Summarize the following medical conversation in simple terms so that an average patient can clearly understand: {text}"
    llm_output = run_llm(prompt)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = {"type": "summary_result", "input_text": text, "output": llm_output, "timestamp": timestamp}
    conversations_db.append(response)
    await websocket.send_json(response)

# --- API Endpoints ---
@app.get("/status")
def get_status():
    # --- Endpoint for Electron to check if the server and models are ready ---
    if app_state["models_loaded"]:
        return {"status": "ready"}
    else:
        return {"status": "loading_models"}

@app.get("/", response_class=HTMLResponse)
async def get_index():
    # --- Serves the main frontend HTML file ---
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# --- Core WebSocket Pipeline ---
async def live_transcription_pipeline(websocket: WebSocket):
    # --- This task runs in a loop to perform real-time OCR and NER ---
    global unique_terms, full_transcript_store
    buffer = []
    last_processed_text = ""
    last_seen_text = ""
    prefix_to_ignore = None
    capture_count = 0
    try:
        while True:
            await asyncio.sleep(0.1)
            current_text = capture_and_ocr((REGION_LEFT, REGION_TOP, REGION_WIDTH, REGION_HEIGHT)).replace("\n", " ").strip()
            
            if current_text and current_text != last_seen_text:
                # --- Logic to ignore fixed initial text (e.g., a username) ---
                if capture_count < 1:
                    capture_count += 1
                    prefix_to_ignore = current_text
                    last_seen_text = current_text
                    print(f"INFO: Ignoring initial prefix: '{prefix_to_ignore}'")
                    continue
                
                clean_current_text = current_text
                if prefix_to_ignore and clean_current_text.startswith(prefix_to_ignore):
                    clean_current_text = clean_current_text[len(prefix_to_ignore):].strip()

                # --- Logic to append only new parts of the text to the buffer ---
                if not buffer:
                    buffer.append(clean_current_text)
                else:
                    new_part = clean_current_text
                    if last_processed_text in new_part:
                        new_part = new_part.replace(last_processed_text, "", 1).strip()
                    if new_part:
                        buffer.append(new_part)

                full_transcript_store = " ".join(buffer)
                last_processed_text = clean_current_text
                last_seen_text = current_text
                
                # --- Run NER on the updated transcript ---
                ner_terms = extract_medical_terms(full_transcript_store)
                unique_terms.update(ner_terms)
                
                # --- Send live data to the frontend ---
                await websocket.send_json({
                    "type": "live_text", "sentence": full_transcript_store,
                    "ner_terms": ner_terms, "unique_terms": sorted(list(unique_terms))
                })
    except (WebSocketDisconnect, asyncio.CancelledError):
        print("Live Transcription: Pipeline task cancelled or client disconnected.")

@app.websocket("/ws/ocr_pipeline")
async def websocket_ocr_endpoint(websocket: WebSocket):
    # --- Main WebSocket connection handler ---
    await websocket.accept()
    transcription_task = None
    global unique_terms, full_transcript_store
    while True:
        try:
            message = await websocket.receive_text()
            data = json.loads(message)
            command = data.get("command")

            if command == "start":
                # --- Start the live transcription background task ---
                if transcription_task is None or transcription_task.done():
                    unique_terms.clear()
                    full_transcript_store = ""
                    transcription_task = asyncio.create_task(live_transcription_pipeline(websocket))
            
            elif command == "stop_session":
                # --- Stop the transcription task and generate the final summary ---
                if transcription_task:
                    transcription_task.cancel()
                    transcription_task = None
                
                final_ner_terms = extract_medical_terms(full_transcript_store)
                final_unique_terms = sorted(list(set(final_ner_terms)))
                
                await websocket.send_json({
                    "type": "final_update", "sentence": full_transcript_store,
                    "ner_terms": final_unique_terms, "unique_terms": final_unique_terms
                })
                
                await websocket.send_json({"type": "processing_llm"})
                await process_llm_and_save(websocket, full_transcript_store)

            elif command == "define_term":
                # --- Get a definition for a specific term from the LLM ---
                term = data.get("term")
                level = data.get("level", "Adult")
                prompt_map = {
                    "Child": f"Explain the medical term '{term}' for a child in max 3 sentences.",
                    "Student": f"Explain the medical term '{term}' for a student in max 3 sentences.",
                    "Adult": f"Provide a definition of the medical term '{term}' in max 3 sentences."
                }
                prompt = prompt_map.get(level, prompt_map["Adult"])
                definition = run_llm(prompt)
                await websocket.send_json({"type": "term_definition", "term": term, "definition": definition})
        
        except WebSocketDisconnect:
            print("Client disconnected. Cleaning up active tasks.")
            if transcription_task:
                transcription_task.cancel()
            break
        except Exception as e:
            print(f"An unexpected error occurred in the WebSocket handler: {e}")

# --- PDF Generation and Export ---
def _draw_paragraph(c, text, x, y, max_width, leading=14, font_name="Helvetica", font_size=11):
    # --- Helper function to draw multi-line text with page breaks ---
    c.setFont(font_name, font_size)
    lines = simpleSplit(text or "", font_name, font_size, max_width)
    y_offset = 0
    for line in lines:
        c.drawString(x, y - y_offset, line)
        y_offset += leading
        if (y - y_offset) < 30 * mm: # Check for bottom margin
            c.showPage()
            c.setFont(font_name, font_size)
            y = A4[1] - 20 * mm
            y_offset = 0
    return y - y_offset

@app.post("/api/export_pdf")
async def export_pdf(payload: dict = Body(...)):
    # --- API endpoint to generate a PDF report from session data ---
    title = payload.get("title") or "Medly AI Report"
    transcript = payload.get("transcript") or ""
    summary = payload.get("summary") or ""
    terms = payload.get("terms") or []
    definition_term = payload.get("definition_term") or ""
    definition = payload.get("definition") or ""
    conversation_label = payload.get("conversation_label", "Diagnosis")

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fname = f"medly_{int(time.time())}.pdf"
    fpath = os.path.join(TEMP_DIR, fname)

    c = canvas.Canvas(fpath, pagesize=A4)
    width, height = A4

    # --- PDF styling ---
    SECTION_COLORS = {
        "Summary": colors.HexColor("#0045a0"),
        conversation_label: colors.HexColor("#0045a0"),
        "Key Terms": colors.HexColor("#0045a0"),
        "Key Term Definition": colors.HexColor("#0045a0"),
    }
    HEADER_TITLE_COLOR = colors.HexColor("#003870")
    HEADER_META_COLOR = colors.HexColor("#132d50")
    
    def draw_section_title(text: str, x: float, y: float) -> float:
        c.setFont("Helvetica-Bold", 15)
        c.setFillColor(SECTION_COLORS.get(text, colors.black))
        c.drawString(x, y, text)
        c.setFillColor(colors.black)
        return y - 8 * mm

    # --- Drawing PDF content ---
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(HEADER_TITLE_COLOR)
    c.drawString(20 * mm, height - 20 * mm, title)
    c.setFont("Helvetica", 11)
    c.setFillColor(HEADER_META_COLOR)
    c.drawString(20 * mm, height - 26 * mm, f"Generated at: {ts}")
    c.setFillColor(colors.black)
    y = height - 36 * mm

    y = draw_section_title("Summary", 20 * mm, y)
    y = _draw_paragraph(c, summary, 20 * mm, y, max_width=170 * mm)
    y -= 5 * mm

    y = draw_section_title(conversation_label, 20 * mm, y)
    y = _draw_paragraph(c, transcript, 20 * mm, y, max_width=170 * mm)

    if terms:
        y -= 5 * mm
        y = draw_section_title("Key Terms", 20 * mm, y)
        y = _draw_paragraph(c, ", ".join(terms), 20 * mm, y, max_width=170 * mm)

    if definition_term or definition:
        y -= 5 * mm
        y = draw_section_title("Key Term Definition", 20 * mm, y)
        y = _draw_paragraph(c, f"{definition_term}\n{definition}".strip(), 20 * mm, y, max_width=170 * mm)

    c.showPage()
    c.save()
    
    # --- Return the URL to the generated PDF ---
    return {"url": f"/temp/{fname}"}

# --- Script entry point ---
if __name__ == "__main__":
    run(app, host="127.0.0.1", port=8000)
