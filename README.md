# MedLY by Synaptix

이 앱은 의사의 진단 내용을 실시간으로 인식하고, 복잡한 의학 용어를 환자가 이해하기 쉬운 쉬운 언어로 풀어 설명해 주는 환자 친화적인 서비스입니다. 음성 인식과 의료 전문 자연어 처리(NLP) 기술을 활용하여 의료진과 환자 간의 의사소통 격차를 줄이고, 환자가 자신의 건강 상태를 보다 명확하게 이해할 수 있도록 돕습니다.

---
# Features

- 의사의 음성 진단 내용을 실시간 STT 변환 + LLM 기반 의학 용어 해설
- 단순 번역이 아닌, 환자 문해력을 고려한 친화적 설명 제공
- 의료 전문 LLM 모델을 엣지 환경(NPU 탑재 디바이스)에 최적화
- 환자의 디바이스 또는 병원 내 전용기기에서 실시간 추론 가능
- 단순 STT 기록 + 의미 해설 기능을 하나의 프로세스로 통합
- 클로바노트 등의 아이디어를 참조하되, 실제 의학 용어에 특화된 해설 기능을 강화

## QwenWrapper 클래스
언어 모델을 사용해 의학 용어를 초등학생도 이해할 수 있도록 쉽게 설명해주는 텍스트 생성 클래스입니다.
- 의료 특화 파인튜닝 모델 사용: Qwen2.5-3B 모델을 의료 데이터로 파인튜닝하여 용어 설명에 더 정확하고 적절한 표현 생성.
- 프롬프트 생성: "의학 용어 '___'에 대해서 초등학생도 이해할 수 있도록 쉽게 설명해줘." 형식.
- 모델 응답 처리: 응답 텍스트에서 핵심 설명만 추출해 정제.



## MedicalNerWrapper 클래스
KoElectra 모델을 활용해 의료 문장에서 질병, 치료, 신체 부위 등의 용어를 추출하는 개체명 인식(NER) 모델 클래스입니다.
- KoElectra 기반 파인튜닝된 모델 사용: "SungJoo/medical-ner-koelectra" 모델 활용.
- 디바이스 자동 설정: GPU 사용 가능 시 자동 할당.
- 토큰 → 형태소 → 용어 매핑: MeCab으로 형태소 분석 후 모델 예측 결과와 매핑.
- 개체명 재구성: B-/I- 태그 기반으로 완전한 용어 구성.
- 출력: 중복 제거된 의료 용어 리스트 반환.



## QwenWrapper 클래스
NER(개체명 인식)으로 뽑아낸 전문 의학 용어들을 일반인, 어린이, 비전공자도 이해하기 쉽게 설명합니다.

---

## Synaptix : Team Members

- 배혜은 (baehappygirl@gmail.com)
- 송재민 (jaemin0003@gmail.com)
- 이현서 (info.laurenlee28@gmail.com)
- 임준 (slow0209@korea.ac.kr)
- 한주엽 (hanjooyeob@korea.ac.kr)

---

## Installation and Execution

### 1. 필수 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 2. 모델 압축파일 업로드
- `ner_saved_model.zip`  
- `qwen2.5-3B-lora-medical.zip`

### 3. 실행
Google Colab 또는 로컬 환경에서 `main.py` 또는 노트북 실행

---

## 종속성(Dependencies)

- `torch`, `torchaudio`
- `transformers==4.40.0`
- `konlpy`, `datasets`, `tokenizers`
- `git+https://github.com/openai/whisper.git`

자세한 내용은 `requirements.txt` 참고

---

## 사용법

1. 음성 녹음 진행
2. Whisper로 텍스트 추출  
3. NER 모델로 의료 용어 추출  
4. Qwen 모델로 용어 설명

---

## 라이선스

The MIT License

Copyright (c) 2025 Synaptix

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


### 사용된 모델 및 라이선스
This project includes material from the 4 models below,
which is licensed under the Apache License 2.0:
https://www.apache.org/licenses/LICENSE-2.0

- `SungBeom/whisper-small-ko`
- `SungJoo/medical-ner-koelectra` 
- `Qwen/Qwen2.5-3B`
- `hephaex/mecab-ko`
