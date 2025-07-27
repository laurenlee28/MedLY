import os
import gc
import torch
import torchaudio
from pipeline import MedicalVoicePipeline  # pipeline.py에 전체 클래스 정의 있다고 가정

# Step 1: Input Audio File
audio_input_path = "sample_audio.mp3"

if not os.path.exists(audio_input_path):
    print(f"🛑 입력 파일이 존재하지 않습니다: {audio_input_path}")
    exit(1)

# Step 2: Convert to compatible format
converted_path = "audio.wav"
try:
    waveform, sample_rate = torchaudio.load(audio_input_path)
    torchaudio.save(converted_path, waveform, sample_rate)
    print(f"✅ 변환 완료: '{audio_input_path}' → '{converted_path}'")
except Exception as e:
    print(f"❌ 오디오 파일 변환 실패: {e}")
    exit(1)

# Step 3: Define model configs
whisper_config = {'model_name': 'small'}
ner_config = {'model_weights_path': './ner_saved_model/ner_saved_model/model_weights.pth'}
qwen_config = {'model_path': 'Qwen/Qwen2-1.5B-Instruct'}

# Step 4: Run the pipeline
pipeline = MedicalVoicePipeline(whisper_config, ner_config, qwen_config)
result = pipeline.run(converted_path)

# Step 5: Output
if result:
    print("\n🎯 최종 결과 요약:")
    print(f"📝 텍스트: {result['text']}")
    print(f"🩺 용어: {result['terms']}")
    print("📘 설명:")
    for term, explanation in result['explanations'].items():
        print(f" - {term}: {explanation}")
else:
    print("🛑 파이프라인 실행 실패")
