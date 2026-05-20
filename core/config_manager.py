# core/config_manager.py
import json
import os

CONFIG_FILE = "config.json"

def load_config():
    """config.json 파일을 읽어서 딕셔너리로 반환, 없으면 기본값 생성"""
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "gemini_api_key": "",
            "novelai_api_key": "",
            "global_prompt": "masterpiece, best quality, newest, highres, detailed anime style",
            "negative_prompt": "lowres, {bad anatomy}, {bad hands}, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
            "width": 832,
            "height": 1216,
            "steps": 28,
            "cfg": 5.0,
            "sampler": "k_euler_ancestral"
        }
        save_config(default_config)
        return default_config
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config_data):
    """딕셔너리 데이터를 config.json에 저장"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)