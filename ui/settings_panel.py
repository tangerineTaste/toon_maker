# ui/settings_panel.py
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
                             QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, 
                             QComboBox, QPushButton, QLabel, QHBoxLayout, 
                             QFileDialog, QScrollArea)
from PyQt6.QtCore import Qt, QTimer

class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        # 스크롤바 공간 확보를 위해 패널 너비 증가
        self.setFixedWidth(340) 
        
        # 최상위 베이스 레이아웃
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(5, 5, 5, 5)
        base_layout.setSpacing(10)

        # 콤보박스 (UI에는 노출되지 않으며 데이터 참조용으로 유지)
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["NovelAI (클라우드)", "ComfyUI (로컬)"])

        # --- 스크롤 영역 설정 ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.scroll_content = QWidget()
        layout = QVBoxLayout(self.scroll_content)
        layout.setContentsMargins(5, 5, 10, 5)
        layout.setSpacing(15)

        # 1. API 및 서버 설정 그룹
        api_group = QGroupBox("API 및 서버 설정")
        self.api_layout = QFormLayout(api_group)
        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.novelai_api_key = QLineEdit()
        self.novelai_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.comfy_url_input = QLineEdit()
        self.comfy_url_input.setPlaceholderText("127.0.0.1:8188")
        
        self.api_layout.addRow("Gemini 키:", self.gemini_key_input)
        self.api_layout.addRow("NAI 키:", self.novelai_api_key)      
        self.api_layout.addRow("Comfy 주소:", self.comfy_url_input)   
        layout.addWidget(api_group)

        # 2. 만화 기획안 그룹
        story_group = QGroupBox("만화 기획안")
        story_layout = QVBoxLayout(story_group)
        story_layout.addWidget(QLabel("<b>상황 개요 (스토리 뼈대)</b>"))
        self.story_input = QTextEdit()
        self.story_input.setPlaceholderText("만화의 상황이나 줄거리를 자유롭게 적어주세요")
        story_layout.addWidget(self.story_input)
        
        story_layout.addWidget(QLabel("<b>캐릭터 정보 (외형 태그 등)</b>"))
        self.char_info_input = QTextEdit()
        self.char_info_input.setMaximumHeight(60)
        self.char_info_input.setPlaceholderText("예: 1girl, pink hair, twintails, red eyes, school uniform")
        story_layout.addWidget(self.char_info_input)

        story_layout.addWidget(QLabel("<b>일관성 지침 및 추가 요구항목</b>"))
        self.consistency_input = QTextEdit()
        self.consistency_input.setMaximumHeight(60)
        self.consistency_input.setPlaceholderText("예: 배경은 일관되게, 일관된 캐릭터 복장 유지.")
        story_group.layout().addWidget(self.consistency_input)
        
        cut_layout = QFormLayout()
        self.cut_count_spin = QSpinBox()
        self.cut_count_spin.setRange(2, 5)
        cut_layout.addRow("만화 컷 수 (2~5):", self.cut_count_spin)
        story_layout.addLayout(cut_layout)
        layout.addWidget(story_group)

        # 3. 그림체 및 퀄리티 그룹
        nai_group = QGroupBox("그림체 및 퀄리티 설정")
        nai_base_layout = QVBoxLayout(nai_group)

        self.engine_toggle_btn = QPushButton("현재 엔진: NovelAI (클라우드)")
        self.engine_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.engine_toggle_btn.setCheckable(True)
        self.engine_toggle_btn.setChecked(True)
        self.engine_toggle_btn.clicked.connect(self.on_engine_toggled)
        nai_base_layout.addWidget(self.engine_toggle_btn)

        self.nai_layout = QFormLayout()
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "nai-diffusion-3",              
            "nai-diffusion-furry-3",        
            "nai-diffusion-4-curated-preview", 
            "nai-diffusion-4-full",         
            "nai-diffusion-4-5-curated",    
            "nai-diffusion-4-5-full"        
        ])
        
        # 파일 탐색기 컨테이너 (체크포인트)
        self.ckpt_container = QWidget()
        ckpt_box = QHBoxLayout(self.ckpt_container)
        ckpt_box.setContentsMargins(0, 0, 0, 0)
        self.ckpt_input = QLineEdit()
        self.ckpt_input.setPlaceholderText("모델 파일(.safetensors) 선택")
        self.ckpt_browse_btn = QPushButton("선택")
        self.ckpt_browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ckpt_browse_btn.clicked.connect(self.browse_ckpt)
        ckpt_box.addWidget(self.ckpt_input)
        ckpt_box.addWidget(self.ckpt_browse_btn)

        # 파일 탐색기 컨테이너 (LoRA)
        self.lora_container = QWidget()
        lora_box = QHBoxLayout(self.lora_container)
        lora_box.setContentsMargins(0, 0, 0, 0)
        self.lora_input = QLineEdit()
        self.lora_input.setPlaceholderText("로라 파일 선택 (비우면 원본)")
        self.lora_browse_btn = QPushButton("선택")
        self.lora_browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lora_browse_btn.clicked.connect(self.browse_lora)
        lora_box.addWidget(self.lora_input)
        lora_box.addWidget(self.lora_browse_btn)
        
        self.style_input = QTextEdit()
        self.style_input.setMaximumHeight(60)
        self.global_prompt = QTextEdit()
        self.global_prompt.setMaximumHeight(60)
        self.negative_prompt = QTextEdit()
        self.negative_prompt.setMaximumHeight(60)
        
        self.seed_input = QLineEdit()
        self.seed_input.setPlaceholderText("비워두면 무작위 생성 (-1)")
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(10, 50)
        self.cfg_spin = QDoubleSpinBox()
        self.cfg_spin.setRange(1.0, 10.0)
        self.cfg_spin.setSingleStep(0.5)
        
        self.cfg_rescale_spin = QDoubleSpinBox()
        self.cfg_rescale_spin.setRange(0.0, 1.0)
        self.cfg_rescale_spin.setSingleStep(0.05)
        
        self.noise_schedule_combo = QComboBox()
        self.noise_schedule_combo.addItems(["native", "karras", "exponential"])
        
        self.sampler_combo = QComboBox()
        self.sampler_combo.addItems(["k_euler_ancestral", "k_euler", "euler", "euler_ancestral", "dpmpp_2m","er_sde"])

        self.nai_layout.addRow("NAI 모델:", self.model_combo)
        self.nai_layout.addRow("Comfy 모델:", self.ckpt_container)
        self.nai_layout.addRow("Comfy 로라:", self.lora_container) 
        self.nai_layout.addRow("그림체 태그:", self.style_input)
        self.nai_layout.addRow("공통 태그:", self.global_prompt)
        self.nai_layout.addRow("제외 태그:", self.negative_prompt)
        self.nai_layout.addRow("Seed:", self.seed_input)
        self.nai_layout.addRow("Steps:", self.steps_spin)
        self.nai_layout.addRow("CFG Scale:", self.cfg_spin)
        self.nai_layout.addRow("NAI Rescale:", self.cfg_rescale_spin)
        self.nai_layout.addRow("Sampler:", self.sampler_combo)
        self.nai_layout.addRow("스케줄러:", self.noise_schedule_combo)
        
        nai_base_layout.addLayout(self.nai_layout)
        layout.addWidget(nai_group)
        layout.addStretch()

        # 스크롤 영역 레이아웃 등록
        self.scroll_area.setWidget(self.scroll_content)
        base_layout.addWidget(self.scroll_area)

        # --- 고정 버튼 영역 (스크롤 외부 하단) ---
        self.save_btn = QPushButton("현재 설정 저장하기")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #2E8B57; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }
            QPushButton:hover { background-color: #3CB371; }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        base_layout.addWidget(self.save_btn)

        self.generate_btn = QPushButton("스토리 생성하기")
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.setStyleSheet("""
            QPushButton { background-color: #4A90E2; color: white; font-weight: bold; font-size: 16px; padding: 15px; border-radius: 8px; }
            QPushButton:hover { background-color: #357ABD; }
            QPushButton:disabled { background-color: #888888; }
        """)
        base_layout.addWidget(self.generate_btn)

        self.load_settings()

    def browse_ckpt(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "체크포인트 모델 선택", "", "Model Files (*.safetensors *.ckpt)")
        if file_path:
            self.ckpt_input.setText(os.path.basename(file_path))

    def browse_lora(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "LoRA 파일 선택", "", "Lora Files (*.safetensors *.ckpt)")
        if file_path:
            self.lora_input.setText(os.path.basename(file_path))

    def on_engine_toggled(self, checked):
        if checked:
            self.engine_toggle_btn.setText("현재 엔진: NovelAI (클라우드)")
            self.engine_toggle_btn.setStyleSheet("QPushButton { background-color: #4A90E2; color: white; font-weight: bold; padding: 12px; border-radius: 6px; font-size: 14px; }")
            self.engine_combo.setCurrentIndex(0) 
        else:
            self.engine_toggle_btn.setText("현재 엔진: ComfyUI (로컬)")
            self.engine_toggle_btn.setStyleSheet("QPushButton { background-color: #2E8B57; color: white; font-weight: bold; padding: 12px; border-radius: 6px; font-size: 14px; }")
            self.engine_combo.setCurrentIndex(1) 
            
        self.set_row_visible(self.api_layout, self.novelai_api_key, checked)
        self.set_row_visible(self.api_layout, self.comfy_url_input, not checked)
        
        self.set_row_visible(self.nai_layout, self.model_combo, checked)
        self.set_row_visible(self.nai_layout, self.cfg_rescale_spin, checked)
        
        self.set_row_visible(self.nai_layout, self.ckpt_container, not checked)
        self.set_row_visible(self.nai_layout, self.lora_container, not checked)

        current_scheduler = self.noise_schedule_combo.currentText()
        self.noise_schedule_combo.blockSignals(True)
        self.noise_schedule_combo.clear()
        
        if checked:
            self.noise_schedule_combo.addItems(["native", "karras", "exponential", "polyexponential"])
            self.noise_schedule_combo.setCurrentText(current_scheduler) if current_scheduler in ["native", "karras", "exponential", "polyexponential"] else self.noise_schedule_combo.setCurrentIndex(0)
        else:
            self.noise_schedule_combo.addItems(["normal", "karras", "exponential", "simple", "sgm_uniform", "ddim_uniform"])
            self.noise_schedule_combo.setCurrentText(current_scheduler) if current_scheduler in ["normal", "karras", "exponential", "simple", "sgm_uniform", "ddim_uniform"] else self.noise_schedule_combo.setCurrentIndex(0)
                
        self.noise_schedule_combo.blockSignals(False)

    def set_row_visible(self, layout, field, visible):
        field.setVisible(visible)
        label = layout.labelForField(field)
        if label:
            label.setVisible(visible)

    def load_settings(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.gemini_key_input.setText(config.get("gemini_api_key", ""))
                self.novelai_api_key.setText(config.get("novelai_api_key", ""))
                self.comfy_url_input.setText(config.get("comfy_url", "127.0.0.1:8188"))
                
                eng = config.get("engine", "NovelAI (클라우드)")
                is_nai = "NovelAI" in eng
                self.engine_toggle_btn.setChecked(is_nai)
                self.on_engine_toggled(is_nai) 
                
                self.ckpt_input.setText(config.get("comfy_ckpt", ""))
                self.lora_input.setText(config.get("comfy_lora", "")) 
                self.story_input.setText(config.get("story", ""))
                self.char_info_input.setText(config.get("char_info", ""))
                self.consistency_input.setText(config.get("consistency", ""))
                self.style_input.setText(config.get("art_style", ""))
                
                idx = self.model_combo.findText(config.get("model", "nai-diffusion-3"))
                if idx >= 0: self.model_combo.setCurrentIndex(idx)
                self.global_prompt.setText(config.get("global_prompt", "masterpiece, best quality"))
                self.negative_prompt.setText(config.get("negative_prompt", "lowres, bad anatomy"))
                self.seed_input.setText(str(config.get("seed", "")))
                self.steps_spin.setValue(config.get("steps", 28))
                self.cfg_spin.setValue(config.get("cfg", 5.0))
                self.cfg_rescale_spin.setValue(config.get("cfg_rescale", 0.2))
                self.cut_count_spin.setValue(config.get("cut_count", 5))
                
                s_idx = self.sampler_combo.findText(config.get("sampler", "k_euler_ancestral"))
                if s_idx >= 0: self.sampler_combo.setCurrentIndex(s_idx)
                n_idx = self.noise_schedule_combo.findText(config.get("noise_schedule", "native"))
                if n_idx >= 0: self.noise_schedule_combo.setCurrentIndex(n_idx)
            except Exception:
                pass

    def save_settings(self):
        config = {
            "gemini_api_key": self.gemini_key_input.text().strip(),
            "novelai_api_key": self.novelai_api_key.text().strip(),
            "comfy_url": self.comfy_url_input.text().strip(),
            "engine": self.engine_combo.currentText(), 
            "comfy_ckpt": self.ckpt_input.text().strip(),
            "comfy_lora": self.lora_input.text().strip(), 
            "story": self.story_input.toPlainText().strip(),
            "char_info": self.char_info_input.toPlainText().strip(),
            "consistency": self.consistency_input.toPlainText().strip(),
            "art_style": self.style_input.toPlainText().strip(),
            "model": self.model_combo.currentText(),
            "global_prompt": self.global_prompt.toPlainText().strip(),
            "negative_prompt": self.negative_prompt.toPlainText().strip(),
            "seed": self.seed_input.text().strip(),
            "steps": self.steps_spin.value(),
            "cfg": self.cfg_spin.value(),
            "cfg_rescale": self.cfg_rescale_spin.value(),
            "sampler": self.sampler_combo.currentText(),
            "noise_schedule": self.noise_schedule_combo.currentText(),
            "cut_count": self.cut_count_spin.value()
        }
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.save_btn.setText("저장 완료")
            QTimer.singleShot(1500, self.reset_save_btn)
        except Exception:
            self.save_btn.setText("저장 실패")

    def reset_save_btn(self):
        self.save_btn.setText("현재 설정 저장하기")