import os
import sys
import json
import datetime
import subprocess
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

BASE_DIR = os.path.dirname(__file__)
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
PIPELINE_SCRIPT = os.path.join(BASE_DIR, "model", "run_medical_pipeline.py")

for d in [RECORDINGS_DIR, TEMP_DIR]:
    os.makedirs(d, exist_ok=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/recordings", StaticFiles(directory=RECORDINGS_DIR), name="recordings")

@app.get("/")
async def get():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/history")
async def get_history():
    with open("static/history.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/recordings-data")
async def get_recordings():
    recordings = []
    for filename in os.listdir(RECORDINGS_DIR):
        if filename.endswith('.mp3'):
            filepath = os.path.join(RECORDINGS_DIR, filename)
            timestamp = filename.replace("recording_", "").replace(".mp3", "")
            try:
                formatted_time = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")
            
            json_path = filepath.replace(".mp3", ".json")
            text = "텍스트 없음"
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    text = data.get("text", "텍스트 없음")

            recordings.append({"filename": filename, "timestamp": formatted_time, "text": text})

    recordings.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"recordings": recordings}

# 중략...

@app.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket):
    await websocket.accept()
    print("🎤 WebSocket 연결됨")

    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            webm_path = os.path.join(TEMP_DIR, f"temp_{timestamp}.webm")
            mp3_path = os.path.join(RECORDINGS_DIR, f"recording_{timestamp}.mp3")

            # ✅ 1단계: WebM 저장 디버깅
            with open(webm_path, "wb") as f:
                f.write(audio_bytes)
            print(f"✅ WebM 저장됨: {webm_path} (크기: {os.path.getsize(webm_path)} bytes)")

            try:
                # ✅ 2단계: FFmpeg 변환
                print("🎵 FFmpeg 변환 시작...")
                subprocess.run([
                    "ffmpeg", "-y", "-i", webm_path,
                    "-acodec", "libmp3lame", "-ar", "16000", "-ab", "192k", mp3_path
                ], check=True)
                print(f"✅ MP3 변환 완료: {mp3_path}")

                # ✅ 3단계: 파이프라인 실행
                print("🧠 전체 파이프라인 실행 중...")
                result = subprocess.run(
                    ["python3", PIPELINE_SCRIPT, mp3_path],
                    capture_output=True, text=True
                )
                print("📦 파이프라인 stdout:\n", result.stdout)
                print("📦 파이프라인 stderr:\n", result.stderr)

                # ✅ 결과 JSON 확인
                json_path = mp3_path.replace(".mp3", ".json")
                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as f:
                        output = json.load(f)
                    await websocket.send_text(json.dumps({
                        "status": "success",
                        "filename": os.path.basename(mp3_path),
                        "text": output.get("text", ""),
                        "explanations": output.get("explanations", {})
                    }))
                else:
                    print("❌ JSON 파일 없음")
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "message": "파이프라인 결과 파일이 없습니다"
                    }))
            except subprocess.CalledProcessError as e:
                print(f"❌ FFmpeg 또는 파이프라인 실행 오류: {e}")
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": "실행 중 오류 발생"
                }))
            finally:
                if os.path.exists(webm_path):
                    os.remove(webm_path)

    except WebSocketDisconnect:
        print("👋 WebSocket 연결 종료")
    except Exception as e:
        print(f"❌ WebSocket 예외: {str(e)}")