# Toon Maker (AI 스토리보드 및 웹툰 생성 자동화 도구)

> **Toon Maker**는 대형 언어 모델(LLM)과 이미지 생성 AI를 결합하여, 사용자의 프롬프트를 기반으로 스토리보드를 기획하고 웹툰 형식의 컷 이미지를 자동으로 렌더링하는 데스크톱 애플리케이션입니다. 클라우드 API와 로컬 AI 엔진을 모두 지원하는 하이브리드 아키텍처를 적용하여 확장성과 렌더링 효율성을 극대화했습니다.

---

## 주요 기능 (Key Features)

### 1. 하이브리드 이미지 생성 파이프라인
- **엔진 동적 스위칭:** 클라우드 기반의 **NovelAI**와 로컬 환경의 **ComfyUI** 중 적합한 렌더링 엔진을 런타임에 선택 및 전환할 수 있습니다.
- **ComfyUI 워크플로우 동적 파싱:** - 정적 API 호출 방식의 한계를 극복하고, 사용자의 `workflow_api.json` 파일을 직접 로드하여 파라미터를 동적으로 주입합니다.
  - `UNETLoader`, `LoraManager`, `SpectrumKSampler` 등 하이엔드 커스텀 노드의 구조를 자동 스캔하여 모델명, 프롬프트, 시드(Seed), 스텝(Steps) 등의 설정값을 안전하게 덮어씁니다.
  - 불필요한 TriggerWord 노드 데이터를 렌더링 전 초기화하여 데이터 정합성을 보장합니다.

### 2. LLM 기반 스토리 기획 (Gemini AI)
- Gemini API를 활용하여 사용자가 입력한 상황 개요와 캐릭터 정보를 바탕으로 세부 컷(상황, 대사, 이미지 생성용 태그)을 자동 구성합니다.
- 프롬프트 엔지니어링을 통해 결과물을 규격화된 JSON 형태로 반환받으며, 다양한 연출과 장르를 지원하기 위해 안전 필터(Safety Settings)를 유연하게 조정하도록 설계되었습니다.

### 3. 반응형 및 동적 UI 설계 (PyQt6)
- **동적 폼 제어 (Dynamic Form):** 선택된 렌더링 엔진(NovelAI / ComfyUI)에 따라 필수 파라미터 입력 필드만 화면에 렌더링되도록 가시성을 제어합니다.
- **스크롤 및 레이아웃 최적화:** 설정 항목의 확장을 고려하여 `QScrollArea`를 적용하였으며, 실행 버튼 등 주요 컨트롤은 뷰포트 하단에 고정하여 사용성을 높였습니다.
- **파일 탐색기 연동:** 로컬 모델(`.safetensors`) 및 LoRA 파일을 직접 입력하는 대신 `QFileDialog`를 통해 직관적으로 선택할 수 있습니다.

### 4. 비동기 처리 및 인터랙티브 편집
- **비동기 멀티스레딩:** `QThread` 기반의 워커(Worker) 클래스를 통해 API 통신 및 무거운 로컬 렌더링 작업 시 메인 UI의 멈춤(Freezing) 현상을 방지합니다.
- **실시간 프롬프트 편집 및 부분 재구동:** 코믹 카드 내부에 `QTextEdit`를 탑재하여 사용자가 특정 컷의 프롬프트를 실시간으로 수정하고, 해당 컷만 독립적으로 재렌더링(Reroll)할 수 있습니다.

---

## 시스템 아키텍처 (Directory Structure)

```text
toon_maker/
├── main.py                     # 애플리케이션 진입점 및 초기화
├── core/                       # 백엔드 통신 및 데이터 처리 코어
│   ├── comfyui_client.py       # ComfyUI API 통신 및 워크플로우(JSON) 동적 주입 모듈
│   ├── novelai_client.py       # NovelAI 이미지 생성 API 통신 모듈
│   ├── gemini_client.py        # LLM 스토리보드 생성 및 응답 파싱 모듈
│   ├── config_manager.py       # 환경 설정 파일(config.json) I/O 관리
│   └── workflow_api.json       # (Required) ComfyUI 추출 API 워크플로우 정의 파일
├── ui/                         # 사용자 인터페이스 (PyQt6)
│   ├── main_window.py          # 메인 프레임워크 및 컴포넌트 라우팅
│   ├── settings_panel.py       # 동적 입력 폼 및 환경 설정 UI
│   ├── viewer_panel.py         # 생성 결과물 배치 및 출력 영역
│   └── comic_card.py           # 개별 이미지 컷 출력 및 프롬프트 편집 뷰
└── workers/                    # 비동기 스레드 풀
    ├── storyboard_worker.py    # LLM API 비동기 통신 워커
    └── image_generate_worker.py# 렌더링 API (다중 컷 / 단일 컷) 비동기 통신 워커
```

## 설치 및 실행 방법 (Installation & Usage) 

### 1. 요구 사항 (Prerequisites)
- Python 3.9 이상
- 로컬 엔진 사용 시, ComfyUI 서버(기본 포트: `8188`)가 백그라운드에서 실행 중이어야 합니다.
- ComfyUI 내 설정 메뉴에서 `Enable Dev mode Options`를 활성화한 뒤 추출한 `workflow_api.json` 파일이 `core/` 디렉토리 내에 위치해야 합니다.

### 2. 패키지 의존성 설치
```bash
pip install -r requirements.txt
```
(주요 의존성 라이브러리: PyQt6, requests 등)

### 3. 애플리케이션 실행
```bash
python main.py
```
### 4. 초기 환경 설정 가이드
- 애플리케이션 구동 후, 좌측 설정 패널에서 Gemini API Key 및 NovelAI API Key(클라우드 엔진 사용 시)를 입력합니다.

- 로컬 엔진(ComfyUI)을 사용할 경우, 설정 패널의 엔진 토글 버클을 조작하여 ComfyUI 주소를 확인하고 사용할 체크포인트 모델 및 LoRA 파일을 탐색기로 지정합니다.

- 입력된 모든 환경 설정값은 프로그램 종료 시 config.json에 자동으로 저장되어 다음 실행 시 자동으로 로드됩니다.

---
추가적으로 문서화가 필요한 내용이나 시스템 명세에 변경 사항이 생기면 언제든 말씀해 주십시오. 즉시 반영하겠습니다.