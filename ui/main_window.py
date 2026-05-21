# ui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QMessageBox
from PyQt6.QtCore import Qt
from ui.settings_panel import SettingsPanel
from ui.viewer_panel import ViewerPanel
from workers.storyboard_worker import StoryboardWorker
from workers.image_generate_worker import ImageGenerateWorker
from ui.comic_card import ComicCard
from core.config_manager import load_config
from workers.image_generate_worker import SingleCutWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 코믹스 엔진 데스크탑 GUI")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet("""
            QToolTip { 
                background-color: #2D2D2D; 
                color: white; 
                border: 2px solid #555; 
                border-radius: 4px;
                font-size: 14px; 
                padding: 8px; 
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.settings_panel = SettingsPanel()
        self.viewer_panel = ViewerPanel()
        
        splitter.addWidget(self.settings_panel)
        splitter.addWidget(self.viewer_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        main_layout.addWidget(splitter)
        
        # 버튼 활성화 
        self.settings_panel.generate_btn.clicked.connect(self.start_generation)
        self.single_workers = {}

        self.connect_card_signals()

    def connect_card_signals(self):
        """뷰어가 카드를 연결"""
        for i in range(1, 6):
            if i in self.viewer_panel.cards:
                try:
                    self.viewer_panel.cards[i].generate_requested.disconnect()
                except TypeError:
                    pass
                self.viewer_panel.cards[i].generate_requested.connect(self.on_single_cut_requested)

    def setup_grid(self):
        """툴팁 만들 때 리롤 버튼 연결하기"""
        self.viewer_panel.clear_viewer()
        for i in range(1, 6):
            card = ComicCard(i)
            card.generate_requested.connect(self.on_single_cut_requested) 
            self.viewer_panel.cards[i] = card
        
        self.viewer_panel.grid_layout.addWidget(self.viewer_panel.cards[1], 0, 0, 1, 5) 
        self.viewer_panel.grid_layout.addWidget(self.viewer_panel.cards[2], 1, 0, 1, 2)
        self.viewer_panel.grid_layout.addWidget(self.viewer_panel.cards[3], 1, 2, 1, 3)
        self.viewer_panel.grid_layout.addWidget(self.viewer_panel.cards[4], 2, 0, 1, 3)
        self.viewer_panel.grid_layout.addWidget(self.viewer_panel.cards[5], 2, 3, 1, 2)

    def start_generation(self):
        """스토리 생성 버튼을 누르면 가장 먼저 실행됨"""
        # 현재 UI에 입력된 설정 먼저 저장
        self.settings_panel.save_settings()
        story = self.settings_panel.story_input.toPlainText()
        char_info = self.settings_panel.char_info_input.toPlainText().strip()
        consistency = self.settings_panel.consistency_input.toPlainText().strip()
        cut_count = self.settings_panel.cut_count_spin.value()
        gemini_key = self.settings_panel.gemini_key_input.text().strip()

        if not story or not gemini_key:
            QMessageBox.warning(self, "경고", "Gemini API 키와 상황 개요를 입력해 주세요!")
            return
        
        self.viewer_panel.reset_grid(cut_count) 

        self.connect_card_signals()
        
        self.settings_panel.generate_btn.setEnabled(False)
        self.settings_panel.generate_btn.setText("스토리 생성 중... ⏳")

        # 워커 출동 로직 (기존과 동일)
        self.story_worker = StoryboardWorker(gemini_key, story, char_info, consistency, cut_count)
        self.story_worker.success_signal.connect(self.on_storyboard_success)
        self.story_worker.error_signal.connect(self.on_worker_error)
        self.story_worker.start()


    def on_storyboard_success(self, storyboard_list):
        """제미나이가 스토리 생성 후 메인 화면에 출력"""
        self.settings_panel.generate_btn.setEnabled(True)
        self.settings_panel.generate_btn.setText("스토리 생성 완료. 컷별로 생성하세요")
        
        for cut in storyboard_list:
            seq_num = cut.get("sequence_number")
            if seq_num in self.viewer_panel.cards:
                # 그림 업데이트(X) 텍스트 이니셜라이즈(O)
                self.viewer_panel.cards[seq_num].initialize_text(
                    cut.get("situation_kr", ""), 
                    cut.get("dialogue", ""), 
                    cut.get("image_prompt", "")
                )
    def on_single_cut_requested(self, seq_num, situation, dialogue, prompt):
        """카드에서 생성/리롤 버튼 누르면 이미지 생성 요청"""
        # 현재 좌측 패널 설정값 긁어오기 (기존 self.get_current_config() 활용)
        config = {
            "novelai_api_key": self.settings_panel.novelai_api_key.text(),
            "art_style": self.settings_panel.style_input.toPlainText(),
            "global_prompt": self.settings_panel.global_prompt.toPlainText(),
            "negative_prompt": self.settings_panel.negative_prompt.toPlainText(),
            "seed": self.settings_panel.seed_input.text().strip(),
            "steps": self.settings_panel.steps_spin.value(),
            "cfg": self.settings_panel.cfg_spin.value(),
            "cfg_rescale": self.settings_panel.cfg_rescale_spin.value(),
            "sampler": self.settings_panel.sampler_combo.currentText(),
            "cut_count": self.settings_panel.cut_count_spin.value(),
            "noise_schedule": self.settings_panel.noise_schedule_combo.currentText(),
            "model": self.settings_panel.model_combo.currentText()
        }
        
        worker = SingleCutWorker(config, seq_num, prompt)
        worker.finished_signal.connect(self.on_single_cut_finished)
        worker.error_signal.connect(self.on_single_cut_error)
        
        self.single_workers[seq_num] = worker # 가비지 컬렉션(삭제) 방지용 보관
        worker.start()

    def on_single_cut_finished(self, seq_num, img_bytes):
        """이미지 수신시 해당 카드에 삽입 """
        if seq_num in self.viewer_panel.cards:
            self.viewer_panel.cards[seq_num].update_image(img_bytes)

    def on_single_cut_error(self, seq_num, error_msg):
        # 에러 나면 다시 버튼 활성화시켜주기
        if seq_num in self.viewer_panel.cards:
            self.viewer_panel.cards[seq_num].gen_btn.setEnabled(True)
            self.viewer_panel.cards[seq_num].gen_btn.setText("❌ 오류 발생 (다시 시도)")
        print(f"[{seq_num}번 컷 오류]: {error_msg}")

    def on_cut_generated(self, seq_num, situation, dialogue, prompt, img_bytes):
        """이미지가 한 장 도착할 때마다 호출됨"""
        if seq_num in self.viewer_panel.cards:
            self.viewer_panel.cards[seq_num].update_content(situation, dialogue, prompt, img_bytes)
        else:
            from ui.comic_card import ComicCard
            extra_card = ComicCard(seq_num)
            extra_card.update_content(situation, dialogue, prompt, img_bytes)
            self.viewer_panel.grid_layout.addWidget(extra_card, seq_num, 0, 1, 5)

    def on_all_finished(self):
        """모든 컷이 다 생성되었을 때 실행"""
        self.settings_panel.generate_btn.setEnabled(True)
        self.settings_panel.generate_btn.setText("스토리 생성 완료)")

    def on_worker_error(self, error_msg):
        """중간에 에러 터졌을 때 실행"""
        self.settings_panel.generate_btn.setEnabled(True)
        self.settings_panel.generate_btn.setText("스토리 생성 ")
        QMessageBox.critical(self, "오류 발생", f"작업 중 오류 발생:\n{error_msg}")