# workers/image_generate_worker.py (전체 덮어쓰기 💦)
import time
from PyQt6.QtCore import QThread, pyqtSignal
from core.novelai_client import generate_novelai_image
from core.comfyui_client import generate_comfyui_image

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
        LANDSCAPE = (1216, 832)
        PORTRAIT = (832, 1216)
        SQUARE = (1024, 1024)
        if seq_num == 1: return LANDSCAPE  
        elif seq_num == 2: return PORTRAIT   
        elif seq_num == 3: return SQUARE     
        elif seq_num == 4: return SQUARE     
        elif seq_num == 5: return PORTRAIT   
        return PORTRAIT

    def run(self):
        try:
            for cut in self.storyboard_list:
                if not self._is_running: break

                seq_num = cut.get("sequence_number", 1)
                situation = cut.get("situation_kr", "상황 설명 누락")
                dialogue = cut.get("dialogue", "...")
                
                art_style = self.config.get("art_style", "")
                base_prompt = self.config.get("global_prompt", "")
                cut_prompt = cut.get("image_prompt", "")
                final_prompt = f"{art_style},{base_prompt}, {cut_prompt}".strip(", ")
                target_width, target_height = self.get_optimal_size(seq_num)

                try:
                    engine_type = self.config.get("engine", "NovelAI (클라우드)")
                    
                    if "NovelAI" in engine_type:
                        api_key = self.config.get("novelai_api_key", "").strip()
                        img_bytes = generate_novelai_image(
                            api_key=api_key, 
                            prompt=final_prompt, 
                            neg_prompt=self.config.get("negative_prompt", ""),
                            width=target_width, height=target_height,   
                            steps=self.config.get("steps", 28), 
                            cfg=self.config.get("cfg", 5.0),
                            sampler=self.config.get("sampler", "k_euler_ancestral"),
                            model=self.config.get("model", "nai-diffusion-4-5-full"),
                            seed=self.config.get("seed", ""),
                            cfg_rescale=self.config.get("cfg_rescale", 0.2),
                            noise_schedule=self.config.get("noise_schedule", "native")
                        )
                    else:
                        server_url = self.config.get("comfy_url", "127.0.0.1:8188")
                        
                        # 🚨 스케줄러 이름 강제 세탁 (native -> normal) 😈
                        scheduler = self.config.get("noise_schedule", "native")
                        if scheduler == "native": scheduler = "normal"
                        
                        img_bytes = generate_comfyui_image(
                            server_url=server_url,
                            prompt=final_prompt, 
                            neg_prompt=self.config.get("negative_prompt", ""),
                            width=target_width, height=target_height,
                            steps=self.config.get("steps", 28), 
                            cfg=self.config.get("cfg", 5.0),
                            sampler=self.config.get("sampler", "euler_ancestral"),
                            scheduler=scheduler, # 👈 췍!
                            ckpt_name=self.config.get("ckpt_name", ""),
                            lora_name=self.config.get("lora_name", ""), # 👈 로라 투입!
                            seed=self.config.get("seed", "")
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
    finished_signal = pyqtSignal(int, bytes)
    error_signal = pyqtSignal(int, str)

    def __init__(self, config, seq_num, prompt):
        super().__init__()
        self.config = config
        self.seq_num = seq_num
        self.prompt = prompt

    def get_optimal_size(self, seq_num):
        LANDSCAPE = (1216, 832)
        PORTRAIT = (832, 1216)
        SQUARE = (1024, 1024)
        if seq_num == 1: return LANDSCAPE  
        elif seq_num == 2: return PORTRAIT   
        elif seq_num == 3: return SQUARE     
        elif seq_num == 4: return SQUARE     
        elif seq_num == 5: return PORTRAIT 
        return PORTRAIT

    def run(self):
        try:
            base_prompt = self.config.get("global_prompt", "")
            art_style = self.config.get("art_style", "")
            prompt_parts = [base_prompt, art_style, self.prompt]
            final_prompt = ", ".join([p.strip() for p in prompt_parts if p.strip()])
            target_width, target_height = self.get_optimal_size(self.seq_num)
            
            engine_type = self.config.get("engine", "NovelAI (클라우드)")

            if "NovelAI" in engine_type:
                api_key = self.config.get("novelai_api_key", "").strip()
                img_bytes = generate_novelai_image(
                    api_key=api_key, 
                    prompt=final_prompt, 
                    neg_prompt=self.config.get("negative_prompt", ""),
                    width=target_width, height=target_height,
                    steps=self.config.get("steps", 28), 
                    cfg=self.config.get("cfg", 5.0),
                    sampler=self.config.get("sampler", "k_euler_ancestral"),
                    model=self.config.get("model", "nai-diffusion-4-5-full"),
                    seed=self.config.get("seed", ""),
                    cfg_rescale=self.config.get("cfg_rescale", 0.2),
                    noise_schedule=self.config.get("noise_schedule", "native")
                )
            else:
                server_url = self.config.get("comfy_url", "127.0.0.1:8188")
                
                # 🚨 여기도 스케줄러 세탁 완! 💕
                scheduler = self.config.get("noise_schedule", "native")
                if scheduler == "native": scheduler = "normal"
                
                img_bytes = generate_comfyui_image(
                    server_url=server_url,
                    prompt=final_prompt, 
                    neg_prompt=self.config.get("negative_prompt", ""),
                    width=target_width, height=target_height,
                    steps=self.config.get("steps", 28), 
                    cfg=self.config.get("cfg", 5.0),
                    sampler=self.config.get("sampler", "euler_ancestral"),
                    scheduler=scheduler, # 👈 투입!
                    ckpt_name=self.config.get("ckpt_name", ""),
                    lora_name=self.config.get("lora_name", ""), # 👈 로라 투입!
                    seed=self.config.get("seed", "")
                )
                
            self.finished_signal.emit(self.seq_num, img_bytes)
            
        except Exception as e:
            self.error_signal.emit(self.seq_num, str(e))