# -*- coding: utf-8 -*-
import argparse
import subprocess
import os

def run_llm(text: str):
    # --- Executes genie-t2t-run.exe and extracts text between [BEGIN]: and [END] ---
    
    # --- Define paths for the LLM executable and config ---
    bundle_dir = r"C:\Users\Qualcomm\Desktop\Syaptix\App\model\phi\genie_bundle"
    executable_path = os.path.join(bundle_dir, "genie-t2t-run.exe")
    config_path = os.path.join(bundle_dir, "genie_config.json")
    
    # --- Construct the prompt in the required format ---
    prompt = f"<|im_start|>system\nYou are a helpful AI Assistant<|im_end|><|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n"
    cmd = [executable_path, "-c", config_path, "-p", prompt]

    try:
        # --- Run the executable as a subprocess ---
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=bundle_dir
        )

        if result.stdout:
            # --- Core logic to parse the raw output ---
            raw_output = result.stdout
            start_marker = "[BEGIN]:"
            end_marker = "[END]"

            # --- 1. Check if both start and end markers exist ---
            if start_marker in raw_output and end_marker in raw_output:
                
                # --- 2. Split by the start marker and take the second part ---
                part_after_begin = raw_output.split(start_marker, 1)[1]
                
                # --- 3. Split the result by the end marker and take the first part ---
                extracted_text = part_after_begin.split(end_marker, 1)[0]
                
                # --- 4. Return the cleaned, stripped text ---
                return extracted_text.strip()
            else:
                # --- If markers are not found, return the raw output as a fallback ---
                return raw_output.strip()
        
        elif result.stderr:
            return f"Error executing LLM (.exe): {result.stderr.strip()}"
            
        return ""

    except FileNotFoundError:
        return f"LLM executable not found: {executable_path}"
    except Exception as e:
        return f"Exception during LLM processing: {e}"
    
def main():
    # --- Main execution function for the script ---
    
    # --- Set up argument parser to accept text from the command line ---
    parser = argparse.ArgumentParser(description="Run the LLM with a given text prompt.")
    parser.add_argument("--text", type=str, required=True, help="Text to process with the LLM.")
    args = parser.parse_args()

    # --- Call the run_llm function with the provided text ---
    result_text = run_llm(args.text)
    
    # --- Print the final result to standard output ---
    # This allows the calling process (e.g., main.py) to capture the result.
    print(result_text)

if __name__ == "__main__":
    main()
