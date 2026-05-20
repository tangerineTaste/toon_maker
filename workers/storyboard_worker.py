# workers/storyboard_worker.py
import json
import time
import os
from PyQt6.QtCore import QThread, pyqtSignal
from core.gemini_client import generate_storyboard

class StoryboardWorker(QThread):
    # 메인 GUI와 소통할 시그널 정의 
    success_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, api_key, story, char_info, cut_count):
        super().__init__()
        pass # 임시
        self.api_key = api_key
        self.story = story
        self.char_info = char_info
        self.cut_count = cut_count

    def run(self):
        try:
            file_path = "debug_storyboard.json"
            
            # 파일이 있는지 체크부터! 
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"{file_path} 파일이 폴더에 없어요! 파일부터 넣어주셈!")

            # 🟢 제미나이 API 쏘는 척하면서 로컬 파일 몰래 읽어오기 
            with open(file_path, "r", encoding="utf-8") as f:
                storyboard_list = json.load(f)

            time.sleep(1.0)
            
            # 파싱한 리스트 메인 UI로 쏴서, 바로 NovelAI 이미지 워커한테 토스! 
            self.success_signal.emit(storyboard_list)
        
        # try:
        #     if not self.api_key:
        #         raise ValueError("Gemini API Key가 누락되었습니다! 좌측에서 입력 후 저장해 주세요. ")
            
        #     # 제미나이 api 가동 
        #     storyboard_list = generate_storyboard(
        #         self.api_key, self.story, self.char_info, self.cut_count
        #     )

        #     # API로 받아온 json 저장
        #     with open("debug_storyboard.json", "w", encoding="utf-8") as f:
        #         json.dump(storyboard_list, f, ensure_ascii=False, indent=2)
        #     print("json 저장 완료! (debug_storyboard.json 열어보셈)")
            
        #     # 성공 시 결과 리스트 장전해서 메인 GUI로 발사! 
        #     self.success_signal.emit(storyboard_list)
            
        except Exception as e:
            # 터지면 에러 메시지 출력
            self.error_signal.emit(str(e))