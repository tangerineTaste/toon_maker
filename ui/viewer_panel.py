from PyQt6.QtWidgets import QWidget, QGridLayout, QScrollArea, QHBoxLayout,QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class ViewerPanel(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        
        self.setStyleSheet("""
            QScrollArea { border: none; background-color: #5A5A5A; }
            QWidget#scrollAreaWidgetContents { background-color: #5A5A5A; }
        """) 
        
        self.container = QWidget()
        self.container.setObjectName("scrollAreaWidgetContents")
        
        self.main_layout = QVBoxLayout(self.container) 
        self.main_layout.setContentsMargins(40, 40, 40, 40) 
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop) 
        
        self.page_widget = QWidget()
        self.page_widget.setObjectName("ComicPage")
        
        self.page_widget.setFixedSize(860, 1216) 
        
        self.page_widget.setStyleSheet("""
            QWidget#ComicPage {
                background-color: #FFFFFF; 
                border: 5px solid #111111; 
            }
        """)
        
        self.page_layout = QVBoxLayout(self.page_widget)
        self.page_layout.setContentsMargins(20, 15, 20, 20)
        self.page_layout.setSpacing(5)

        self.header_label = QLabel("PAGE 1")
        self.header_label.setStyleSheet("font-size: 20px; font-weight: 900; color: #111111; border: none; border-bottom: 4px solid #111111; padding-bottom: 5px;")
        self.page_layout.addWidget(self.header_label)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        
        self.grid_layout.setSpacing(0) 
        self.grid_layout.setContentsMargins(0, 5, 0, 0) 
        
        self.page_layout.addWidget(self.grid_container)
        self.page_layout.setStretchFactor(self.grid_container, 1)
        
        self.cards = {}
        self.setup_grid()
        
        self.main_layout.addWidget(self.page_widget)
        self.setWidget(self.container)

    def setup_grid(self, cut_count=5):
        """선택한 컷 수(2~5)에 맞춰서 프레임을 원고지 안에 배치"""
        self.clear_viewer()
        from ui.comic_card import ComicCard

        if cut_count == 5:
            self.page_widget.setFixedSize(860, 1600)
        else:
            self.page_widget.setFixedSize(860, 1216)

        def add_card(seq_num, row, col, row_span, col_span):
            card = ComicCard(seq_num)
            self.cards[seq_num] = card
            self.grid_layout.addWidget(card, row, col, row_span, col_span)

        if cut_count == 2:
            add_card(1, 0, 0, 1, 2)
            add_card(2, 0, 2, 1, 3)
        elif cut_count == 3:
            add_card(1, 0, 0, 1, 5)
            add_card(2, 1, 0, 1, 2)
            add_card(3, 1, 2, 1, 3)
        elif cut_count == 4:
            add_card(1, 0, 0, 1, 5)
            add_card(2, 1, 0, 1, 2)
            add_card(3, 1, 2, 1, 3)
            add_card(4, 2, 0, 1, 5)
        else:
            add_card(1, 0, 0, 1, 5)
            add_card(2, 1, 0, 1, 2)
            add_card(3, 1, 2, 1, 3)
            add_card(4, 2, 0, 1, 3)
            add_card(5, 2, 3, 1, 2)

            self.grid_layout.setRowStretch(0, 5) 
            self.grid_layout.setRowStretch(1, 4) 
            self.grid_layout.setRowStretch(2, 4)
        
        for i in range(5):
            self.grid_layout.setColumnStretch(i, 1)

    def clear_viewer(self):
        """뷰어 비우기 (초기화용)"""
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.cards.clear()
        
    def reset_grid(self, cut_count):
        """새로 시작할 때 컷 수 받아서 리셋"""
        self.setup_grid(cut_count)