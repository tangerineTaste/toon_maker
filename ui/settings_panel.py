# ui/settings_panel.py
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
                             QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, 
                             QComboBox, QPushButton, QLabel)
from PyQt6.QtCore import Qt, QTimer

class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(320)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 1. 🔑 API 인증 그룹
        api_group = QGroupBox("🔑 API 인증")
        api_layout = QFormLayout(api_group)
        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.novelai_api_key = QLineEdit()
        self.novelai_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("Gemini 키:", self.gemini_key_input)
        api_layout.addRow("NAI 키:", self.novelai_api_key)
        layout.addWidget(api_group)

        # 2. 📝 만화 기획안
        story_group = QGroupBox("📝 만화 기획안")
        story_layout = QVBoxLayout(story_group)

        story_layout.addWidget(QLabel("<b>📖 상황 개요 (스토리 뼈대)</b>"))
        self.story_input = QTextEdit()
        self.story_input.setPlaceholderText("만화의 상황이나 줄거리를 자유롭게 적어주세요")
        story_layout.addWidget(self.story_input)
        
        story_layout.addWidget(QLabel("<b>✨ 캐릭터 정보 (외형 태그 등)</b>"))
        self.char_info_input = QTextEdit()
        self.char_info_input.setMaximumHeight(60)
        self.char_info_input.setPlaceholderText("예: 1girl, pink hair, twintails, red eyes, school uniform")
        self.cut_count_spin = QSpinBox()
        self.cut_count_spin.setRange(2, 5)
        
        
        story_layout.addWidget(self.char_info_input)
        cut_layout = QFormLayout()
        cut_layout.addRow("🎬 만화 컷 수 (2~5):", self.cut_count_spin)
        story_layout.addLayout(cut_layout)
        layout.addWidget(story_group)

        # 3. 🎨 그림체 & 퀄리티
        nai_group = QGroupBox("🎨 그림체 & 퀄리티")
        nai_layout = QFormLayout(nai_group)
        self.global_prompt = QTextEdit()
        self.global_prompt.setMaximumHeight(60)
        self.negative_prompt = QTextEdit()
        self.negative_prompt.setMaximumHeight(60)
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(10, 50)
        self.cfg_spin = QDoubleSpinBox()
        self.cfg_spin.setRange(1.0, 10.0)
        self.cfg_spin.setSingleStep(0.5)
        self.sampler_combo = QComboBox()
        self.sampler_combo.addItems(["k_euler_ancestral", "k_euler", "k_dpmpp_2s_ancestral", "k_dpmpp_2m"])

        nai_layout.addRow("공통 태그:", self.global_prompt)
        nai_layout.addRow("제외 태그:", self.negative_prompt)
        nai_layout.addRow("Steps:", self.steps_spin)
        nai_layout.addRow("CFG Scale:", self.cfg_spin)
        nai_layout.addRow("Sampler:", self.sampler_combo)
        layout.addWidget(nai_group)

        layout.addStretch()

        self.save_btn = QPushButton("💾 현재 설정 저장하기")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #2E8B57; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }
            QPushButton:hover { background-color: #3CB371; }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_btn)

        self.generate_btn = QPushButton("스토리 생성하기")
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.setStyleSheet("""
            QPushButton { background-color: #4A90E2; color: white; font-weight: bold; font-size: 16px; padding: 15px; border-radius: 8px; }
            QPushButton:hover { background-color: #357ABD; }
            QPushButton:disabled { background-color: #888888; }
        """)
        layout.addWidget(self.generate_btn)

        self.load_settings()

    def load_settings(self):
        """config.json 읽어서 설정 불러오기"""
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                self.gemini_key_input.setText(config.get("gemini_api_key", ""))
                self.novelai_api_key.setText(config.get("novelai_api_key", ""))
                self.global_prompt.setText(config.get("global_prompt", "masterpiece, best quality, very aesthetic, absurdres"))
                self.negative_prompt.setText(config.get("negative_prompt", "lowres, bad anatomy, bad hands, text, error, missing fingers, worst quality, low quality"))
                self.steps_spin.setValue(config.get("steps", 28))
                self.cfg_spin.setValue(config.get("cfg", 5.0))
                self.cut_count_spin.setValue(config.get("cut_count", 5))
                
                sampler = config.get("sampler", "k_euler_ancestral")
                idx = self.sampler_combo.findText(sampler)
                if idx >= 0:
                    self.sampler_combo.setCurrentIndex(idx)
            except Exception as e:
                print(f"config.json 오류 발생 (로드 실패): {e}")

    def save_settings(self):
        """현재 입력된 값들을 config.json으로 저장"""
        config = {
            "gemini_api_key": self.gemini_key_input.text().strip(),
            "novelai_api_key": self.novelai_api_key.text().strip(),
            "global_prompt": self.global_prompt.toPlainText().strip(),
            "negative_prompt": self.negative_prompt.toPlainText().strip(),
            "steps": self.steps_spin.value(),
            "cfg": self.cfg_spin.value(),
            "sampler": self.sampler_combo.currentText(),
            "cut_count": self.cut_count_spin.value()
        }
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            self.save_btn.setText("✅ 저장 완료! (config.json)")
            self.save_btn.setStyleSheet("QPushButton { background-color: #32CD32; color: black; font-weight: bold; padding: 10px; border-radius: 5px; }")
            
            # 1.5초 뒤에 원래 버튼으로 원상복구
            QTimer.singleShot(1500, self.reset_save_btn)
        except Exception as e:
            print(f"config.json 오류 발생 (저장 실패): {e}")
            self.save_btn.setText("❌ 저장 실패 (콘솔 확인)")

    def reset_save_btn(self):
        self.save_btn.setText("💾 현재 설정 저장하기")
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #2E8B57; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }
            QPushButton:hover { background-color: #3CB371; }
        """)