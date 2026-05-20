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
        
        LANDSCAPE = (1216, 832)  # 가로형
        PORTRAIT = (832, 1216)   # 세로형
        SQUARE = (1024, 1024)    # 정방형

        if cut_count == 2:
            if seq_num == 1: return PORTRAIT    
            if seq_num == 2: return PORTRAIT    
        elif cut_count == 3:
            if seq_num == 1: return LANDSCAPE   
            if seq_num == 2: return PORTRAIT
            if seq_num == 3: return SQUARE
        elif cut_count == 4:
            if seq_num == 1: return LANDSCAPE
            if seq_num == 2: return PORTRAIT
            if seq_num == 3: return SQUARE
            if seq_num == 4: return LANDSCAPE   
        else: 
            if seq_num == 1: return LANDSCAPE  
            if seq_num == 2: return PORTRAIT   
            if seq_num == 3: return SQUARE     
            if seq_num == 4: return SQUARE     
            if seq_num == 5: return PORTRAIT  
            
        return PORTRAIT

    def run(self):
        try:
            api_key = self.config.get("novelai_api_key", "").strip()
            
            for cut in self.storyboard_list:
                if not self._is_running: break

                seq_num = cut.get("sequence_number", 1)
                situation = cut.get("situation_kr", "상황 설명 누락")
                dialogue = cut.get("dialogue", "...")
                
                art_style = self.config.get("art_style", "")
                base_prompt = self.config.get("global_prompt", "")
                cut_prompt = cut.get("image_prompt", "")
                final_prompt = f"{art_style},{base_prompt}, {cut_prompt}".strip(", ")
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

        cut_count = self.config.get("cut_count", 5)

        LANDSCAPE = (1216, 832)  # 가로형
        PORTRAIT = (832, 1216)   # 세로형
        SQUARE = (1024, 1024)    # 정방형

        if cut_count == 2:
            if seq_num == 1: return PORTRAIT    
            if seq_num == 2: return PORTRAIT    
        elif cut_count == 3:
            if seq_num == 1: return LANDSCAPE   
            if seq_num == 2: return PORTRAIT
            if seq_num == 3: return SQUARE
        elif cut_count == 4:
            if seq_num == 1: return LANDSCAPE
            if seq_num == 2: return PORTRAIT
            if seq_num == 3: return SQUARE
            if seq_num == 4: return LANDSCAPE   
        else: 
            if seq_num == 1: return LANDSCAPE  
            if seq_num == 2: return PORTRAIT   
            if seq_num == 3: return SQUARE     
            if seq_num == 4: return SQUARE     
            if seq_num == 5: return PORTRAIT 
            
        return PORTRAIT

    def run(self):
        try:
            api_key = self.config.get("novelai_api_key", "").strip()
            art_style = self.config.get("art_style", "")
            base_prompt = self.config.get("global_prompt", "")
            final_prompt = f"{art_style},{base_prompt}, {self.prompt}".strip(", ")
            
            target_width, target_height = self.get_optimal_size(self.seq_num)

            img_bytes = generate_novelai_image(
                api_key=api_key, 
                prompt=final_prompt, 
                neg_prompt=self.negative_prompt,
                width=target_width, 
                height=target_height,
                steps=self.config.get("steps", 28), 
                cfg=self.config.get("cfg", 5.0),
                sampler=self.config.get("sampler", "k_euler_ancestral"),
                model=self.config.get("model", "nai-diffusion-3"),
                seed=self.config.get("seed", ""),
                cfg_rescale=self.config.get("cfg_rescale", 0.2),
                noise_schedule=self.config.get("noise_schedule", "native")
            )
            self.finished_signal.emit(self.seq_num, img_bytes)
        except Exception as e:
            self.error_signal.emit(self.seq_num, str(e))