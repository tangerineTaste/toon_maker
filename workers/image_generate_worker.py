# workers/image_generate_worker.py
import time
from PyQt6.QtCore import QThread, pyqtSignal
from core.novelai_client import generate_novelai_image

class ImageGenerateWorker(QThread):
    cut_finished_signal = pyqtSignal(int, str, str, str, bytes)
    error_signal = pyqtSignal(str)
    all_finished_signal = pyqtSignal()

    def __init__(self, config, storyboard_list):
        super().__init__()
        self.config = config
        self.storyboard_list = storyboard_list
        self._is_running = True

    def get_optimal_size(self, seq_num):
        cut_count = self.config.get("cut_count", 5)
        
        if cut_count == 2:
            if seq_num == 1: return 512, 768    # 2칸 넓이
            if seq_num == 2: return 704, 768    # 3칸 넓이
        elif cut_count == 3:
            if seq_num == 1: return 1216, 448   # 5칸 통짜 와이드
            if seq_num == 2: return 512, 768
            if seq_num == 3: return 704, 768
        elif cut_count == 4:
            if seq_num == 1: return 1216, 448
            if seq_num == 2: return 512, 768
            if seq_num == 3: return 704, 768
            if seq_num == 4: return 1216, 448   # 바닥 와이드
        else: 
            # 5컷 국룰 레이아웃
            if seq_num == 1: return 1216, 448
            if seq_num == 2: return 512, 768
            if seq_num == 3: return 704, 768
            if seq_num == 4: return 704, 768
            if seq_num == 5: return 512, 768
            
        return 832, 1216 

    def run(self):
        try:
            api_key = self.config.get("novelai_api_key", "").strip()
            
            for cut in self.storyboard_list:
                if not self._is_running: break

                seq_num = cut.get("sequence_number", 1)
                situation = cut.get("situation_kr", "상황 설명 누락")
                dialogue = cut.get("dialogue", "...")
                
                base_prompt = self.config.get("global_prompt", "")
                cut_prompt = cut.get("image_prompt", "")
                final_prompt = f"{base_prompt}, {cut_prompt}".strip(", ")
                negative_prompt = self.config.get("negative_prompt", "")

                
                target_width, target_height = self.get_optimal_size(seq_num)

                try:
                    img_bytes = generate_novelai_image(
                        api_key=api_key, 
                        prompt=final_prompt, 
                        neg_prompt=negative_prompt,
                        width=target_width,     
                        height=target_height,   
                        steps=self.config.get("steps", 28), 
                        cfg=self.config.get("cfg", 5.0),
                        sampler=self.config.get("sampler", "k_euler_ancestral")
                    )

                    self.cut_finished_signal.emit(seq_num, situation, dialogue, final_prompt, img_bytes)
                except Exception as e:
                    self.error_signal.emit(f"[{seq_num}번 컷 오류 발생]: {str(e)}")
                
                time.sleep(1.0)
            self.all_finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))

    def stop(self):
        self._is_running = False

class SingleCutWorker(QThread):
    """한 컷만 이미지 생성 (리롤 전용)"""
    finished_signal = pyqtSignal(int, bytes) # 컷 번호, 이미지
    error_signal = pyqtSignal(int, str)

    def __init__(self, config, seq_num, prompt):
        super().__init__()
        self.config = config
        self.seq_num = seq_num
        self.prompt = prompt
        self.negative_prompt = config.get("negative_prompt", "")

    def get_optimal_size(self, seq_num):
        if seq_num == 1: return 1216, 448   
        elif seq_num == 2: return 512, 768    
        elif seq_num == 3: return 704, 768    
        elif seq_num == 4: return 704, 768    
        elif seq_num == 5: return 512, 768    
        else: return 832, 1216   

    def run(self):
        try:
            api_key = self.config.get("novelai_api_key", "").strip()
            base_prompt = self.config.get("global_prompt", "")
            final_prompt = f"{base_prompt}, {self.prompt}".strip(", ")
            
            target_width, target_height = self.get_optimal_size(self.seq_num)

            img_bytes = generate_novelai_image(
                api_key=api_key, 
                prompt=final_prompt, 
                neg_prompt=self.negative_prompt,
                width=target_width, 
                height=target_height,
                steps=self.config.get("steps", 28), 
                cfg=self.config.get("cfg", 5.0),
                sampler=self.config.get("sampler", "k_euler_ancestral")
            )
            self.finished_signal.emit(self.seq_num, img_bytes)
        except Exception as e:
            self.error_signal.emit(self.seq_num, str(e))