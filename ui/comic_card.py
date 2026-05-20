# ui/comic_card.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect, QScrollArea, QPushButton
from PyQt6.QtGui import QPixmap, QImage, QPainter, QCursor
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal

class ComicImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self.setMinimumSize(100, 100)
        self.setStyleSheet("border: 3px solid black;") 

        
    def set_pixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        if self._pixmap.isNull():
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        scaled_pixmap = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        x = (self.width() - scaled_pixmap.width()) // 2
        y = (self.height() - scaled_pixmap.height()) // 2
        painter.drawPixmap(x, y, scaled_pixmap)

class ComicCard(QWidget):
    generate_requested = pyqtSignal(int, str, str, str) 

    def __init__(self, seq_num, parent=None):
        super().__init__(parent)
        self.seq_num = seq_num
        self.setMouseTracking(True)
        self.text_ready = False # 대본이 도착했는지 체크하는 플래그 
        self.cut_data = {} # 대본 텍스트 임시 저장소
        
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = ComicImageLabel()

        self.image_label.setText(f"컷 {seq_num}\n대기 중... ⏳")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            background-color: #FFFFFF; 
            border: 3px solid #111111; 
            color: #72AEE6; 
            font-size: 22px; 
            font-weight: 900;
            font-family: 'Malgun Gothic', sans-serif;
        """)
        base_layout.addWidget(self.image_label)
        
        # 블랙아웃 오버레이
        self.overlay = QWidget(self)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 210); border: 3px solid black;") 
        self.overlay.hide()
        
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_area = QScrollArea(self.overlay)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; } QWidget#scroll_container { background: transparent; }")
        
        self.scroll_container = QWidget()
        self.scroll_container.setObjectName("scroll_container")
        scroll_layout = QVBoxLayout(self.scroll_container)
        
        self.desc_label = QLabel(self.scroll_container)
        self.desc_label.setWordWrap(True)
        scroll_layout.addWidget(self.desc_label)
        
        self.gen_btn = QPushButton("🎨 이 컷 그림 생성하기")
        self.gen_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.gen_btn.setStyleSheet("""
            QPushButton { background-color: #FFD700; color: black; font-weight: bold; border-radius: 5px; padding: 12px; font-size: 15px; margin-top: 10px; }
            QPushButton:hover { background-color: #FFA500; }
            QPushButton:disabled { background-color: #555; color: #888; }
        """)
        self.gen_btn.clicked.connect(self.on_btn_clicked)
        scroll_layout.addWidget(self.gen_btn)
        
        self.scroll_area.setWidget(self.scroll_container)
        overlay_layout.addWidget(self.scroll_area)
        
        self.opacity_effect = QGraphicsOpacityEffect(self.overlay)
        self.overlay.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0) 
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(250) 
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad) 

    def on_btn_clicked(self):
        """버튼 누르면 메인 UI로 렌더링 요청"""
        self.gen_btn.setEnabled(False)
        self.gen_btn.setText("그림 깎는 중... ⏳ (Rerolling)")
        self.generate_requested.emit(self.seq_num, self.cut_data['situation'], self.cut_data['dialogue'], self.cut_data['prompt'])

    def resizeEvent(self, event):
        if self.overlay:
            self.overlay.resize(self.image_label.size())
            self.overlay.move(self.image_label.pos())
        super().resizeEvent(event)

    def enterEvent(self, event):
        """마우스 들어올 때: 그림이 완성된 상태일 때만 애니메이션"""
        if not self.image_label._pixmap.isNull(): 
            self.overlay.show()
            self.anim.stop() 
            self.anim.setStartValue(self.opacity_effect.opacity())
            self.anim.setEndValue(1.0) 
            self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """마우스 나갈 때: 그림이 완성된 상태일 때만 패널 숨김"""
        if self.overlay.isVisible() and not self.image_label._pixmap.isNull():
            self.anim.stop()
            self.anim.setStartValue(self.opacity_effect.opacity())
            self.anim.setEndValue(0.0)
            self.anim.finished.connect(lambda: self.overlay.hide() if self.opacity_effect.opacity() == 0.0 else None)
            self.anim.start()
        super().leaveEvent(event)

    def initialize_text(self, situation, dialogue, prompt):
        """제미나이가 JSON 대본 줬을 때 (그림 없는 상태)"""
        self.cut_data = {'situation': situation, 'dialogue': dialogue, 'prompt': prompt}
        self.text_ready = True
        
        html_content = (
            f"<div style='font-family: Malgun Gothic, sans-serif; color: #EEEEEE; line-height: 1.5;'>"
            f"  <span style='font-size: 16px; font-weight: bold; color: #4A90E2;'>🎬 [컷 {self.seq_num}] 상황:</span><br>"
            f"  <span style='font-size: 14px;'>{situation}</span><br><br>"
            f"  <span style='font-size: 18px; font-weight: bold; color: #FFD700;'>💬 대사:</span><br>"
            f"  <span style='font-size: 20px; font-weight: bold; color: white;'>{dialogue}</span><br><br>"
            f"  <span style='font-size: 13px; font-weight: bold; color: #AAAAAA;'>✨ 프롬프트:</span><br>"
            f"  <span style='font-size: 12px; color: #888888;'>{prompt}</span>"
            f"</div>"
        )
        self.desc_label.setText(html_content)
        self.image_label.setText("") 
        
        self.gen_btn.setText("🎨 이 컷 그림 생성하기")
        self.gen_btn.setEnabled(True)

        self.overlay.show()
        self.opacity_effect.setOpacity(0.0) 
        
        self.anim.stop()
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0) 
        self.anim.start()

    def update_image(self, img_bytes):
        """그림 깎아왔을 때"""
        image = QImage.fromData(img_bytes)
        pixmap = QPixmap.fromImage(image)
        self.image_label.setText("")
        self.image_label.set_pixmap(pixmap)
        self.image_label.setStyleSheet("border: 3px solid black; background-color: transparent;") 
        
        self.gen_btn.setText("🎲 다시 그리기 (Reroll)") 
        self.gen_btn.setEnabled(True)

        if self.overlay.isVisible():
            self.anim.stop()
            self.anim.setStartValue(self.opacity_effect.opacity())
            self.anim.setEndValue(0.0) # 0% 투명도로 페이드아웃
            self.anim.finished.connect(lambda: self.overlay.hide() if self.opacity_effect.opacity() == 0.0 else None)
            self.anim.start()