import pyautogui
import pytesseract
import time
from datetime import datetime
from PIL import Image
import cv2
import numpy as np
import subprocess
import os
import sys

# --- Set the path to the Tesseract OCR engine executable ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Define paths for development vs. packaged environments ---
def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT_DIR = get_app_path()
QWEN_SCRIPT = os.path.join(ROOT_DIR, "model", "phi", "genie_bundle", "run_qwen.py")

# --- Define the screen region to capture for OCR ---
REGION_LEFT = 0
REGION_TOP = 90
REGION_WIDTH = 2700
REGION_HEIGHT = 90

# --- Variables for batching text to send to the LLM ---
last_processed_time = time.time()
TEXT_BUFFER = []
PROCESS_INTERVAL = 30  # Process the buffer every 30 seconds

# --- Variables for sentence completion logic ---
last_text = ""
current_sentence_buffer = ""
last_text_update_time = time.time()
TIMEOUT_SECONDS = 5.0 # Consider a sentence complete after 5s of no new text

def capture_and_ocr(region):
    # --- Captures and performs OCR on a specified screen region ---
    try:
        screenshot = pyautogui.screenshot(region=region)
        screenshot_np = np.array(screenshot)
        gray_image = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)
        _, binary_image = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY_INV)
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(binary_image, lang='kor+eng', config=custom_config)
        return text.strip()
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

def process_text_buffer():
    # --- Sends the buffered complete sentences to the LLM script ---
    global TEXT_BUFFER
    if not TEXT_BUFFER:
        return

    combined_text = " ".join(TEXT_BUFFER)
    TEXT_BUFFER = []  # Clear the buffer after processing

    try:
        cmd = [sys.executable, QWEN_SCRIPT, "--text", combined_text]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT_DIR, encoding='utf-8')

        print("\n" + "="*20 + " LLM Processing Result " + "="*20)
        print(f"Input Text: {combined_text}")
        if result.stdout:
             print(f"LLM Output: {result.stdout.strip()}")
        if result.stderr:
             print(f"LLM Error/Log: {result.stderr.strip()}")
        print("="*58 + "\n")

    except Exception as e:
        print(f"Error during LLM processing: {e}")

def main():
    # --- Main loop to continuously capture, process, and buffer text ---
    global last_text, current_sentence_buffer, last_text_update_time, last_processed_time
    print("Starting real-time OCR... (Press Ctrl+C to stop)")
    
    try:
        while True:
            capture_region = (REGION_LEFT, REGION_TOP, REGION_WIDTH, REGION_HEIGHT)
            current_text = capture_and_ocr(capture_region).strip()
            
            # --- 1. Process only if there's a meaningful change in text ---
            if current_text and current_text != last_text:
                last_text_no_space = last_text.replace(" ", "")
                current_text_no_space = current_text.replace(" ", "")

                # --- 2. If the new text extends the old one (e.g., "hello" -> "hello world") ---
                if current_text_no_space.startswith(last_text_no_space):
                    current_sentence_buffer = current_text
                    print(f"Updating sentence: {current_sentence_buffer}")
                # --- 3. If it's a completely new sentence ---
                else:
                    if current_sentence_buffer:
                        print(f"\nSentence complete (new text detected): '{current_sentence_buffer}'")
                        TEXT_BUFFER.append(current_sentence_buffer)
                    
                    current_sentence_buffer = current_text
                    print(f"New sentence started: {current_sentence_buffer}")

                last_text_update_time = time.time()
                last_text = current_text

            # --- 4. If there's a pause, consider the sentence complete ---
            if current_sentence_buffer and (time.time() - last_text_update_time) > TIMEOUT_SECONDS:
                print(f"\nSentence complete (timeout): '{current_sentence_buffer}'")
                TEXT_BUFFER.append(current_sentence_buffer)
                
                current_sentence_buffer = ""
                last_text = ""

            # --- 5. Periodically send the buffered sentences to the LLM ---
            if (time.time() - last_processed_time) >= PROCESS_INTERVAL:
                process_text_buffer()
                last_processed_time = time.time()
            
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        print("\nTest finished.")

if __name__ == "__main__":
    main()
