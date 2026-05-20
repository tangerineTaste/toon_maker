# AI 코믹스 엔진 데스크탑 GUI 

## 1. 프로젝트 개요
사용자가 간단한 상황만 입력하면 AI가 컷 단위로 연출을 짜고 그림까지 알아서 그려주는 '실전 압축 웹툰 자동 연출 및 생성기'입니다. 
텍스트 입력 한 번에 즉시 웹툰이 생산되는 고효율을 목표로 개발되었습니다. 

## 2. 핵심 기능 (현재까지 구현 완료) 
* **자동 스토리 생성 (Gemini API):** 상황 개요와 캐릭터 정보만 던져주면 Gemini가 알아서 컷을 분할하고, 대사를 치고, Danbooru 프롬프트까지 완벽한 JSON 배열 형태로 짜옵니다. 

* **만화 원고지 UI (PyQt6):**  가로 860px 세로 1216px 비율의 원고지 템플릿을 구현했습니다. 사용자가 지정한 컷 수(2~5컷)에 맞춰 테트리스처럼 그리드가 자동 분할됩니다. 
* **설정 자동 저장 시스템:** 입력된 설정(Gemini/NAI 키, 프롬프트, 해상도 등)을 `config.json`에 영구 저장하고 불러옵니다. 

## 3. 프로젝트 구조
[cite_start]디렉토리 구조는 다음과 같습니다. 
```text
project/
├── main.py
├── config.json
├── requirements.txt
├── core/
│   ├── gemini_client.py
│   ├── novelai_client.py
│   ├── image_utils.py
│   ├── config_manager.py
│   └── webtoon_exporter.py
├── workers/
│   ├── storyboard_worker.py
│   └── image_generate_worker.py
├── ui/
│   ├── main_window.py
│   ├── settings_panel.py
│   ├── viewer_panel.py
│   └── comic_card.py
├── cache/
├── output/
└── temp/
```