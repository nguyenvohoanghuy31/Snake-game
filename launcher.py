import sys
import subprocess
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QCheckBox, QSpacerItem,
    QSizePolicy, QMessageBox, QGraphicsDropShadowEffect,
    QStyle
)
from PySide6.QtGui import (
    QFont, QPalette, QColor, QBrush, QPixmap, QIcon, QLinearGradient,
    QFontDatabase  
)
from PySide6.QtCore import Qt, QTimer, QSize
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        try:
            import codecs # Import codecs nếu cần
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
        except Exception:
            pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HIGHSCORE_FILE = os.path.join(SCRIPT_DIR, "highscore.txt")
GAME_SCRIPT_FILE = os.path.join(SCRIPT_DIR, "game.py")
BACKGROUND_IMAGE_FILE = os.path.join(SCRIPT_DIR, "background.png")


CUSTOM_FONT_FILENAME = "font.ttf"
CUSTOM_FONT_PATH = os.path.join(SCRIPT_DIR, CUSTOM_FONT_FILENAME)



def load_custom_font():

    default_font_list = "'Segoe UI', 'Tahoma', 'Arial'" 
    
    if not os.path.exists(CUSTOM_FONT_PATH):
        print(f"Lưu ý: Không tìm thấy '{CUSTOM_FONT_FILENAME}'. Dùng font hệ thống.")
        return default_font_list

    try:
        font_id = QFontDatabase.addApplicationFont(CUSTOM_FONT_PATH)
        if font_id == -1:
            print(f"Lỗi: Không thể tải '{CUSTOM_FONT_FILENAME}'. Dùng font hệ thống.")
            return default_font_list
        
        family_names = QFontDatabase.applicationFontFamilies(font_id)
        if not family_names:
            print(f"Lỗi: Không tìm thấy tên family cho '{CUSTOM_FONT_FILENAME}'. Dùng font hệ thống.")
            return default_font_list

        loaded_family_name = family_names[0]
        print(f"Đã tải font tùy chỉnh: '{loaded_family_name}' từ {CUSTOM_FONT_FILENAME}")
        
        return f"'{loaded_family_name}', {default_font_list}"

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tải font: {e}. Dùng font hệ thống.")
        return default_font_list


class SnakeLauncher(QMainWindow):
    def __init__(self, font_family): # Thêm 'font_family' làm tham số
        super().__init__()
        self.game_process = None
        self.check_process_timer = QTimer(self)
        self.check_process_timer.timeout.connect(self.check_game_status)
        
        self.font_family = font_family 
        
        self.init_ui()
        self.update_background() 

    def add_shadow_effect(self, widget, blur_radius=15, offset_y=3):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, offset_y)
        widget.setGraphicsEffect(shadow)

    def init_ui(self):
        self.setWindowTitle("Snake Game Launcher")
        self.resize(1100, 700)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        self.title_label = QLabel("SNAKE\nGAME")
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.add_shadow_effect(self.title_label, blur_radius=25, offset_y=5) 

        # --- Hiển thị Điểm cao ---
        self.high_score_label = QLabel()
        self.high_score_label.setObjectName("HighScoreLabel")
        self.high_score_label.setAlignment(Qt.AlignCenter)
        self.add_shadow_effect(self.high_score_label, blur_radius=10, offset_y=2)
        self.update_high_score()

        # --- Nút Bắt đầu (Liquid Glass) ---
        self.start_button = QPushButton("START GAME")
        self.start_button.setObjectName("StartButton")
        self.start_button.setMinimumHeight(70)
        self.start_button.clicked.connect(self.start_game)
        icon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self.start_button.setIcon(icon)
        self.start_button.setIconSize(QSize(28, 28))

        # --- Checkbox Chế độ Wrap ---
        self.wrap_checkbox = QCheckBox("Special Mode")
        self.wrap_checkbox.setObjectName("WrapCheckbox")
        self.add_shadow_effect(self.wrap_checkbox, blur_radius=10, offset_y=2)

        # --- Thêm các widget vào layout ---
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        main_layout.addWidget(self.title_label)
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        main_layout.addWidget(self.high_score_label)
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Fixed))
        main_layout.addWidget(self.start_button)
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        main_layout.addWidget(self.wrap_checkbox, alignment=Qt.AlignCenter)
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setCentralWidget(central_widget)

        self.setStyleSheet(self.get_stylesheet(self.font_family))

    def get_stylesheet(self, font_family_default): 
        

        title_font_size = 80
        ui_font_size = 18
        checkbox_font_size = 20
        button_font_size = 22


        return f"""
            #TitleLabel {{
                font-family: {font_family_default}; /* <-- Sử dụng font từ tham số */
                font-size: {title_font_size}px;
                font-weight: 900;
                color: #668cff; 
                background-color: transparent;
                border: none;
                padding-top: 10px;
                padding-bottom: 10px;
                line-height: 0.9;
            }}

            #HighScoreLabel {{
                font-family: {font_family_default}; /* <-- Sử dụng font từ tham số */
                font-size: {ui_font_size}px;
                font-weight: bold;
                color: #ff751a;
                padding: 10px;
                background-color: transparent;
                border-radius: 5px;
            }}

            #StartButton {{
                font-family: {font_family_default}; /* <-- Sử dụng font từ tham số */
                font-size: {button_font_size}px;
                font-weight: bold;
                color: #FFFFFF;
                padding: 10px;
                border-radius: 15px;
                background-color: rgba(255, 255, 255, 0.15); 
                border: 1px solid rgba(255, 255, 255, 0.3);
                text-align: center;
                padding-left: 20px;
            }}
            #StartButton:hover {{
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.6);
            }}
            #StartButton:disabled {{
                background-color: rgba(0, 0, 0, 0.4);
                color: #BBBBBB;
                border: 1px solid rgba(0, 0, 0, 0.5);
            }}

            #WrapCheckbox {{
                font-family: {font_family_default}; /* <-- Sử dụng font từ tham số */
                font-size: {checkbox_font_size}px;
                font-weight: bold;
                color: #FFB700;
                spacing: 10px;
                background-color: transparent;
                padding: 5px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                background-color: rgba(0, 0, 0, 0.5);
                border: 2px solid #555;
                border-radius: 5px;
            }}
            QCheckBox::indicator:checked {{
                background-color: #76FF03;
                border: 2px solid #B2FF59;
            }}
        """


    def load_high_score(self):
        try:
            with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                return int(f.read())
        except (FileNotFoundError, ValueError):
            return 0

    def update_high_score(self):
        score = self.load_high_score()
        self.high_score_label.setText(f"HIGH SCORE: {score}")

    def start_game(self):
        if not os.path.exists(GAME_SCRIPT_FILE):
            QMessageBox.critical(self, "Lỗi",
                f"Không tìm thấy tệp '{os.path.basename(GAME_SCRIPT_FILE)}'.\n"
                f"Hãy chắc chắn rằng bạn đã lưu tệp game Pygame của mình với tên '{os.path.basename(GAME_SCRIPT_FILE)}' "
                "trong cùng thư mục với launcher.")
            return

        wrap_enabled = self.wrap_checkbox.isChecked()
        command = [sys.executable, GAME_SCRIPT_FILE]
        if wrap_enabled:
            command.append('--wrap')

        try:
            self.game_process = subprocess.Popen(command)
            self.start_button.setEnabled(False)
            self.start_button.setText("GAME IS RUNNING...")
            self.hide()
            self.check_process_timer.start(1000)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể khởi chạy {os.path.basename(GAME_SCRIPT_FILE)}: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        self.update_background()
        super().resizeEvent(event)

    def update_background(self):
        palette = QPalette()
        pixmap = QPixmap(BACKGROUND_IMAGE_FILE)
        
        if pixmap.isNull():
            print(f"Lỗi: Không tìm thấy ảnh nền tại: {BACKGROUND_IMAGE_FILE}")
            print("Sử dụng nền gradient dự phòng.")
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0.0, QColor(20, 50, 20))
            gradient.setColorAt(1.0, QColor(10, 10, 10))
            palette.setBrush(QPalette.Window, QBrush(gradient))
        else:
            scaled_pixmap = pixmap.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            palette.setBrush(QPalette.Window, QBrush(scaled_pixmap))
            
        self.setPalette(palette)

    def check_game_status(self):
        if self.game_process and self.game_process.poll() is not None:
            self.game_process = None
            self.check_process_timer.stop()
            self.start_button.setEnabled(True)
            self.start_button.setText("START GAME")
            self.update_high_score()
            self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    loaded_font_family = load_custom_font()
    
    if not os.path.exists(BACKGROUND_IMAGE_FILE):
        QMessageBox.warning(None, "Thiếu tệp",
            f"Không tìm thấy ảnh nền '{os.path.basename(BACKGROUND_IMAGE_FILE)}'.\n"
            f"Hãy đảm bảo bạn đã lưu ảnh vào cùng thư mục với launcher.\n"
            "Chương trình sẽ chạy với nền mặc định.")

    window = SnakeLauncher(font_family=loaded_font_family)
    

    window.show()

    try:

        screen = QApplication.primaryScreen()
        available_geometry = screen.availableGeometry()
        screen_center = available_geometry.center()
        
        window_frame = window.frameGeometry()
        
        window_frame.moveCenter(screen_center)
        window.move(window_frame.topLeft())
    except Exception as e:
        print(f"Lưu ý: Không thể căn giữa cửa sổ. Lỗi: {e}")
    
    sys.exit(app.exec())