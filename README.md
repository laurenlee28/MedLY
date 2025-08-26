<div align="center">

# 🏥 Medly: A Patient-Friendly Medical Phraseology App

**An on-device AI app that provides real-time explanations of medical terms to improve communication between patients and doctors.**

<p>
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/ONNX--Runtime-lightgrey?style=for-the-badge&logo=onnx&logoColor=black" alt="ONNX Runtime">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT">
</p>

</div>

<div align="center">
  
### 🎬 **Execution Video**
</div>
<div align="center">
  <a href="https://www.youtube.com/watch?v=cnXvFwt4Krc">
  <img src="https://i.ytimg.com/vi/cnXvFwt4Krc/hqdefault.jpg" alt="Watch the video" />
</a>
</div>


---
### 📝 **Purpose**

> **"Difficult medical terms are no longer a barrier."**

**Medly** is an innovative solution that leverages the NPU performance of the Snapdragon X Elite to analyze speech in real time and instantly convert complex medical jargon into easy-to-understand everyday language for patients. The project was launched to address the asymmetry of medical information, helping patients gain a deeper understanding of their condition and actively participate in their medical care.

### ✅ NPU Leverage
* **Ultra-low Latency Performance**
The NPU delivers faster performance on speech recognition and medical terminology tagging compared to CPU or GPU inference. This ensures patients and providers see explanations in real time with minimal lag.

* **High Energy Efficiency**
Its low-power design allows the AI to run continuously throughout a consultation without draining the device's battery.

* **Excellent Security and Data Privacy**
All AI computations are processed directly on the device, ensuring data privacy by keeping sensitive patient data from ever leaving the device.

---
## ✨ Key Features
| Feature | Description |
|   ---   | --- |
| **🎙️ Real-time STT** | Instantly converts voice input from the microphone into text. |
| **🧬 Terminology Recognition** | Accurately identifies and tags medical-related professional terms from the text. |
| **💡 Simplified Explanations** | AI analyzes the meaning of recognized professional terms to provide easy-to-understand explanations and summaries. |
| **📜 Comprehensive Summary** | Provides a complete summary of the entire voice conversation. |
| **📄 PDF Report Generation** | Generates a PDF report that summarizes your diagnosis and allows for printing. |
| **👨‍👩‍👧‍👦 Adjustable Difficulty** | Enables setting the explanation difficulty level (Child, Student, Adult) by adjusting the LLM's prompts. |
| **💻 On-Device Processing** | All AI computations are processed directly on the device's NPU for maximum speed and security. |

---
## 🛠️ Tech Stack
**💻 Hardware Requirements (Tested device)**
```text
Device: Galaxy Book4 Edge
Chip: Snapdragon® X Elite X1E-80-100
OS: Windows 11 Home
Memory: 16 GB LPDDR5X Memory
Storage: 512 GB eUFS
NPU: Qualcomm® Hexagon™ NPU
```
**📚 Software Requirements**
```text
Transcription: Live Caption & Tesseract OCR
Named Entity Recognition: d4data/biomedical-ner-all
LLM Provider: Qualcomm QNN
Chat Model: Qwen2.5_7B_Instruct
Python: 3.12.X (Recommended)
```
---
## ⚙️ Installation

This application utilizes open-source models (such as Qwen, NER, and OCR) that have been optimized for NPU performance through conversion to the ONNX file format.

Because some of these large model files exceed GitHub's 50MB size limit, the complete installer is provided via an external link. (We are currently sharing it via Google Drive but plan to deploy it on a hosting service like Vercel in the future).

- 1. [Download the installer from Google Drive](https://drive.google.com/file/d/1wwKbO_GOdcS1Q69XhurM3SzMPHQvd-x4/view?usp=sharing)

- 2. After the download is complete, run the .exe file to install the application.

---
## 💡 Usage
Follow these steps to use Medly for real-time medical conversation analysis:

- 1. Start Recording: Click the Start button to begin the session. The application will immediately start listening and transcribing the conversation.

- 2. Live Transcription: As you speak, the transcribed text will appear in the Diagnosis area in real-time.

- 3. Stop Recording: Once the conversation is complete, click the Stop button.

- 4. Review Analysis: After a moment, a concise Summary of the conversation will be generated. You will also see a list of important medical terms appear under Key Terms.

- 5. Get Definitions: Click on any term in the Key Terms list. Its definition will be displayed in the Definition panel on the right.

- 6. Adjust Reading Level: You can change the complexity of the term's explanation by selecting the desired level: Child, Student, or Adult.

- 7. Download a Report: Click the Download PDF button to save a report containing the full transcript, summary, and key terms from the session.

- 8. Start a New Session: To clear the current results and begin a new recording, click the New Session button (the "Stop" button becomes "New Session" after a session ends).

---
## 👨‍💻 Synaptix : Team Members

- Hyeeun Bae (baehappygirl@gmail.com)
- Jaemin Song (jaemin0003@gmail.com)
- Hyunseo Lee (info.laurenlee28@gmail.com)
- Joon Lim (slow0209@korea.ac.kr)
- Jooyeob Han (hanjooyeob@korea.ac.kr)

---
## 📜 License
MIT License

Copyright (c) <2025> <Synaptix>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
