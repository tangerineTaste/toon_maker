# ui/lora_manager_dialog.py
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QWidget, QLabel, QPushButton, QLineEdit, QScrollArea, 
                             QCheckBox, QDoubleSpinBox, QFileDialog, QSplitter,
                             QTreeWidget, QTreeWidgetItem)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class LoraCard(QWidget):
    def __init__(self, rel_path, file_path, initial_weight=1.0, is_selected=False, state_callback=None):
        super().__init__()
        self.rel_path = rel_path
        self.file_path = file_path
        self.state_callback = state_callback
        
        # UI 표출용 이름 (확장자 제거 및 경로 정리)
        self.clean_name = os.path.basename(rel_path).replace(".safetensors", "").replace(".ckpt", "")
        
        self.setFixedSize(160, 220)
        self.setStyleSheet("""
            QWidget { background-color: #2D2D2D; border: 1px solid #444; border-radius: 8px; }
            QWidget[selected="true"] { border: 2px solid #4A90E2; background-color: #3A4A5A; }
            QLabel { border: none; background: transparent; color: #EEE; }
        """)
        self.setProperty("selected", is_selected)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(140, 140)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #1A1A1A; border-radius: 4px;")
        
        pixmap = self.load_thumbnail()
        if pixmap:
            self.image_label.setPixmap(pixmap.scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.image_label.setText("No Image")
            
        layout.addWidget(self.image_label)
        
        self.name_label = QLabel(self.clean_name)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.name_label.setToolTip(self.rel_path)
        layout.addWidget(self.name_label)
        
        control_layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(is_selected)
        self.checkbox.stateChanged.connect(self.notify_state_change)
        
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0.1, 3.0)
        self.weight_spin.setSingleStep(0.1)
        self.weight_spin.setValue(initial_weight)
        self.weight_spin.setStyleSheet("background-color: #111; color: white; border: 1px solid #555;")
        self.weight_spin.valueChanged.connect(self.notify_state_change)
        
        control_layout.addWidget(self.checkbox)
        control_layout.addStretch()
        control_layout.addWidget(self.weight_spin)
        layout.addLayout(control_layout)

    def load_thumbnail(self):
        base_dir = os.path.dirname(self.file_path)
        base_name = os.path.splitext(os.path.basename(self.file_path))[0]
        extensions = [".png", ".jpg", ".jpeg", ".preview.png"]
        
        for ext in extensions:
            img_path = os.path.join(base_dir, base_name + ext)
            if os.path.exists(img_path):
                return QPixmap(img_path)
        return None

    def notify_state_change(self):
        is_selected = self.checkbox.isChecked()
        weight = self.weight_spin.value()
        
        self.setProperty("selected", is_selected)
        self.style().unpolish(self)
        self.style().polish(self)
        
        if self.state_callback:
            self.state_callback(self.rel_path, is_selected, weight)

    def mousePressEvent(self, event):
        # 카드 영역 클릭 시 체크박스 토글
        self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)


class LoraManagerDialog(QDialog):
    def __init__(self, parent=None, lora_dir="", current_loras_str=""):
        super().__init__(parent)
        self.setWindowTitle("Visual LoRA Manager")
        self.setFixedSize(950, 650)
        
        self.base_lora_dir = lora_dir
        self.current_lora_dir = lora_dir
        self.cards = []
        
        # 전역 선택 상태 관리 (폴더 이동 시 선택 내역 유지)
        self.selected_map = {}
        if current_loras_str:
            for item in current_loras_str.split(","):
                parts = item.split(":")
                name = parts[0].strip()
                weight = float(parts[1].strip()) if len(parts) > 1 else 1.0
                if name:
                    self.selected_map[name] = weight

        self.init_ui()
        self.populate_tree()
        self.scan_current_dir()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 상단 제어부
        top_layout = QHBoxLayout()
        self.dir_input = QLineEdit(self.base_lora_dir)
        self.dir_input.setPlaceholderText("ComfyUI의 models/loras 폴더 루트 경로 지정")
        self.dir_input.setReadOnly(True)
        
        self.browse_btn = QPushButton("루트 폴더 변경")
        self.browse_btn.clicked.connect(self.browse_base_directory)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("하위 폴더 포함 전체 검색...")
        self.search_input.textChanged.connect(self.filter_loras)
        self.search_input.setFixedWidth(200)
        
        top_layout.addWidget(QLabel("Root 폴더:"))
        top_layout.addWidget(self.dir_input)
        top_layout.addWidget(self.browse_btn)
        top_layout.addWidget(self.search_input)
        main_layout.addLayout(top_layout)
        
        # 중앙 분할 영역 (좌측: 폴더 트리, 우측: LoRA 그리드)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        self.tree_widget.setMinimumWidth(200)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll_area.setWidget(self.scroll_widget)
        
        self.splitter.addWidget(self.tree_widget)
        self.splitter.addWidget(self.scroll_area)
        self.splitter.setSizes([250, 700])
        
        main_layout.addWidget(self.splitter)
        
        # 하단 조작부
        btn_layout = QHBoxLayout()
        self.status_label = QLabel(f"선택된 항목: {len(self.selected_map)}개")
        
        btn_layout.addWidget(self.status_label)
        btn_layout.addStretch()
        
        self.apply_btn = QPushButton("선택 항목 적용")
        self.apply_btn.setStyleSheet("background-color: #2E8B57; color: white; font-weight: bold; padding: 8px 16px;")
        self.apply_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.setStyleSheet("padding: 8px 16px;")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        main_layout.addLayout(btn_layout)

    def browse_base_directory(self):
        new_dir = QFileDialog.getExistingDirectory(self, "LoRA Root 폴더 선택", self.base_lora_dir)
        if new_dir:
            self.base_lora_dir = new_dir
            self.current_lora_dir = new_dir
            self.dir_input.setText(self.base_lora_dir)
            self.populate_tree()
            self.scan_current_dir()

    def populate_tree(self):
        self.tree_widget.clear()
        if not os.path.exists(self.base_lora_dir):
            return

        root_name = os.path.basename(os.path.normpath(self.base_lora_dir)) or self.base_lora_dir
        root_item = QTreeWidgetItem(self.tree_widget, [f"📂 {root_name} (Root)"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.base_lora_dir)
        self.tree_widget.addTopLevelItem(root_item)

        self._build_tree_recursive(self.base_lora_dir, root_item)
        root_item.setExpanded(True)

    def _build_tree_recursive(self, current_dir, parent_item):
        try:
            entries = sorted(os.scandir(current_dir), key=lambda e: e.name.lower())
            for entry in entries:
                if entry.is_dir() and not entry.name.startswith('.'):
                    child_item = QTreeWidgetItem([f"📁 {entry.name}"])
                    child_item.setData(0, Qt.ItemDataRole.UserRole, entry.path)
                    parent_item.addChild(child_item)
                    self._build_tree_recursive(entry.path, child_item)
        except PermissionError:
            pass

    def on_tree_item_clicked(self, item, column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and os.path.exists(path):
            self.current_lora_dir = path
            self.search_input.clear() # 트리 이동 시 검색어 초기화
            self.scan_current_dir()

    def clear_grid(self):
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.cards.clear()

    def scan_current_dir(self):
        self.clear_grid()
        if not os.path.exists(self.current_lora_dir):
            return
            
        valid_extensions = [".safetensors", ".ckpt", ".pt"]
        results = []
        
        try:
            for file_name in sorted(os.listdir(self.current_lora_dir), key=str.lower):
                file_path = os.path.join(self.current_lora_dir, file_name)
                if os.path.isfile(file_path) and os.path.splitext(file_name)[1].lower() in valid_extensions:
                    # ComfyUI 처리를 위해 Root 기준 상대 경로로 변환 및 백슬래시 정제
                    rel_path = os.path.relpath(file_path, self.base_lora_dir).replace("\\", "/")
                    results.append((rel_path, file_path))
        except PermissionError:
            pass

        self.populate_grid(results)

    def filter_loras(self, text):
        query = text.lower()
        if not query:
            self.scan_current_dir()
            return

        self.clear_grid()
        if not os.path.exists(self.base_lora_dir):
            return

        valid_extensions = [".safetensors", ".ckpt", ".pt"]
        results = []

        # 검색 시에는 루트부터 하위 폴더까지 전체 스캔을 수행합니다.
        for root, dirs, files in os.walk(self.base_lora_dir):
            for file_name in files:
                if query in file_name.lower() and os.path.splitext(file_name)[1].lower() in valid_extensions:
                    file_path = os.path.join(root, file_name)
                    rel_path = os.path.relpath(file_path, self.base_lora_dir).replace("\\", "/")
                    results.append((rel_path, file_path))

        # 검색 결과는 파일명 기준 오름차순 정렬
        results.sort(key=lambda x: os.path.basename(x[1]).lower())
        self.populate_grid(results)

    def populate_grid(self, file_list):
        columns = 4
        for index, (rel_path, file_path) in enumerate(file_list):
            # 전역 선택 맵에 등록된 상태 확인
            is_selected = rel_path in self.selected_map
            weight = self.selected_map.get(rel_path, 1.0)
            
            card = LoraCard(rel_path, file_path, weight, is_selected, self.on_card_state_changed)
            self.cards.append(card)
            
            row = index // columns
            col = index % columns
            self.grid_layout.addWidget(card, row, col)

    def on_card_state_changed(self, rel_path, is_selected, weight):
        """카드 컴포넌트의 체크 및 가중치 변경 이벤트를 수신하여 전역 상태 갱신"""
        if is_selected:
            self.selected_map[rel_path] = weight
        else:
            if rel_path in self.selected_map:
                del self.selected_map[rel_path]
                
        self.status_label.setText(f"선택된 항목: {len(self.selected_map)}개")

    def get_selected_loras_string(self):
        """전역으로 저장된 선택 맵 데이터를 기반으로 설정 반환 포맷 구성"""
        selected = []
        for rel_path, weight in self.selected_map.items():
            selected.append(f"{rel_path}:{weight:.1f}")
        return ", ".join(selected)