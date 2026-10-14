import sys
import os
import json
import subprocess
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QLineEdit, QDialog,
    QProgressBar, QScrollArea
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Base and Output Directories
if getattr(sys, 'frozen', False):
    BASEDIR = os.path.dirname(sys.executable)
else:
    BASEDIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_PATH = os.path.join(BASEDIR, "Downloads", "nogikoi")
MEMBER_DATA_FILE = os.path.join(BASEDIR, "member_data.json")

# Server and Path References
MAIN_PATH = {
    "server 1": "https://prd-content.static.game.nogikoi.jp",
    "server 2": "https://prd-content-gree.static.game.nogikoi.jp"
}

FILE_PATH = {
    "bg-event": "/assets/img/event/",
    "card-png": "/assets/img/card/mypage/",
    "card-jpg": "/assets/img/card/l/",
    "icon": "/assets/img/member/icon/",
    "sprites": "/assets/img/member/story/",
    "sound": "/assets/sound/"
}

content_option = [
    'bg-event',
    'card-png',
    'card-jpg',
    'icon',
    'sprites',
    'sound'
]

card_color_id = {
    '1': "blue",
    '2': "pink",
    '3': "green"
}

card_star_id = {
    '1': '10',
    '2': '21',
    '3': '30',
    '4': '41',
    '5': '50',
    '6': '61',
    '7': '70',
    '8': '81'
}


def load_member_data():
    """Load member id-to-name mapping from member_data.json."""
    if os.path.exists(MEMBER_DATA_FILE):
        try:
            with open(MEMBER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading member_data.json: {e}")
    return {}


def get_member_versions(member_id_str):
    """
    Return sprite version range according to member generation.
    Generasi 1 dan 2: 2 sampai 6
    Generasi 3 dan 4: 5 sampai 8
    Generasi 5: 6 sampai 8
    Generasi 6: 8
    """
    try:
        mid = int(member_id_str)
    except ValueError:
        return range(2, 9)

    if mid <= 37:
        return range(2, 7)      # Gen 1 & 2: 2 to 6
    elif mid <= 65:
        return range(5, 9)      # Gen 3 & 4: 5 to 8
    elif mid <= 76:
        return range(6, 9)      # Gen 5: 6 to 8
    else:
        return [8]              # Gen 6: 8


def convert_m4a_to_wav(m4a_path):
    """Convert an m4a file to wav using ffmpeg, then remove the original m4a."""
    wav_path = m4a_path.rsplit('.', 1)[0] + '.wav'
    try:
        startupinfo = None
        creationflags = 0
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

        subprocess.run(
            ["ffmpeg", "-y", "-i", m4a_path, wav_path],
            stdin=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=creationflags,
            capture_output=True,
            timeout=60
        )
        if os.path.exists(wav_path):
            os.remove(m4a_path)
        return True
    except Exception:
        return False


class Progress(QThread):
    start_progress = pyqtSignal(str)              # filename
    progress = pyqtSignal(str, int, int)          # filename, downloaded_bytes, total_bytes
    file_done = pyqtSignal(str, bool, str)        # filename, success, message
    all_done = pyqtSignal()

    def __init__(self, download_tasks, option):
        """
        download_tasks: list of dicts with keys:
            - 'url': remote URL to fetch
            - 'dest_path': destination local file path
            - 'filename': display name
            - 'convert_wav': (optional) bool, if True convert m4a to wav after download
        """
        super().__init__()
        self.download_tasks = download_tasks
        self.option = option
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        session = requests.Session()
        for item in self.download_tasks:
            if self._is_cancelled:
                break

            url = item["url"]
            dest_path = item["dest_path"]
            filename = item["filename"]
            need_convert = item.get("convert_wav", False)

            # Check if already converted wav exists
            wav_path = dest_path.rsplit('.', 1)[0] + '.wav' if need_convert else None
            if wav_path and os.path.exists(wav_path):
                self.start_progress.emit(filename)
                self.file_done.emit(filename, True, f"{filename} already exist")
                continue

            self.start_progress.emit(filename)

            if os.path.exists(dest_path):
                # m4a exists but wav doesn't – convert it
                if need_convert:
                    convert_m4a_to_wav(dest_path)
                self.file_done.emit(filename, True, f"{filename} already exist")
                continue

            try:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                response = session.get(url, stream=True, timeout=20)
                if response.status_code == 200:
                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0
                    with open(dest_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if self._is_cancelled:
                                break
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                self.progress.emit(filename, downloaded, total_size)
                    if self._is_cancelled:
                        if os.path.exists(dest_path):
                            os.remove(dest_path)
                        break

                    # Convert m4a to wav if needed
                    if need_convert:
                        convert_m4a_to_wav(dest_path)

                    self.file_done.emit(filename, True, f"{filename} Downloaded")
                else:
                    self.file_done.emit(filename, False, "is not in the server")
            except Exception as e:
                self.file_done.emit(filename, False, str(e))

        self.all_done.emit()


class DownloadProgress(QDialog):
    def __init__(self, download_tasks, option, parent=None):
        super().__init__(parent)
        self.download_tasks = download_tasks
        self.option = option
        self.file_widgets = {}

        self._build_ui()
        self._start_download()

    def _build_ui(self):
        self.setWindowTitle("File Process")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        outer_layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        self.download_layout = QVBoxLayout(content_widget)
        self.download_layout.addStretch()

        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)

        self.scroll = scroll

    def _add_file_widget(self, filename):
        lbl = QLabel(filename.split(".")[0])
        bar = QProgressBar()
        status = QLabel("Downloading...")

        self.download_layout.insertWidget(self.download_layout.count() - 1, lbl)
        self.download_layout.insertWidget(self.download_layout.count() - 1, bar)
        self.download_layout.insertWidget(self.download_layout.count() - 1, status)

        self.file_widgets[filename] = {
            "label": lbl,
            "bar": bar,
            "status": status
        }

        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    def _start_download(self):
        self.downloading = Progress(self.download_tasks, self.option)
        self.downloading.start_progress.connect(self._add_file_widget)
        self.downloading.progress.connect(self._on_progress)
        self.downloading.file_done.connect(self._on_file_done)
        self.downloading.all_done.connect(self._on_all_done)
        self.downloading.start()

    def _on_progress(self, filename: str, downloaded: int, total: int):
        w = self.file_widgets.get(filename)
        if not w:
            return
        if total > 0:
            pct = int(downloaded / total * 100)
            w["bar"].setValue(pct)
            w["bar"].setFormat(f"%p% — {downloaded // 1024} KB / {total // 1024} KB")
        w["status"].setText("⬇️ Downloading...")
        w["status"].setStyleSheet("color: #2196F3;")

    def _on_file_done(self, filename: str, success: bool, message: str):
        w = self.file_widgets.get(filename)
        if not w:
            return
        if "already exist" in message:
            w["bar"].hide()
            w["label"].setText(f'{filename.split(".")[0]} already exist')
            w["label"].setStyleSheet("color: green;")
            w["status"].hide()
            return
        if "is not in the server" in message:
            w["bar"].hide()
            w["label"].setText(f'{filename} is not in the server')
            w["label"].setStyleSheet("color: red;")
            w["status"].hide()
            return

        if success:
            w["bar"].setValue(100)
            w["bar"].setFormat("✅ 100%")
            w["status"].setText(message)
            w["status"].setStyleSheet("color: green;")
        else:
            w["bar"].setFormat("❌ Gagal")
            w["status"].setText(f"Error: {message}")
            w["status"].setStyleSheet("color: red;")

    def _on_all_done(self):
        self.setWindowFlag(Qt.WindowCloseButtonHint, True)
        self.show()

    def closeEvent(self, event):
        if hasattr(self, 'downloading') and self.downloading.isRunning():
            self.downloading.cancel()
            self.downloading.wait(1000)
        event.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        icon_path = self.resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.member_data = load_member_data()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Nogikoi Downloader")
        self.setMinimumSize(400, 220)

        self.window = QWidget()
        self.layout = QVBoxLayout()

        self.server = QComboBox()
        self.server.addItems(MAIN_PATH.keys())

        self.option = QComboBox()
        self.option.addItems(content_option)
        self.option.currentTextChanged.connect(self.option_select)

        self.setCentralWidget(self.window)
        self.window.setLayout(self.layout)
        self.layout.addWidget(self.server)
        self.layout.addWidget(self.option)

        self._dynamic_widgets = []
        self.option_select()

    def _clear_dynamic_widgets(self):
        for widget in self._dynamic_widgets:
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self._dynamic_widgets.clear()

    def option_select(self):
        self._clear_dynamic_widgets()

        current = self.option.currentText()
        if current in ['card-png', 'card-jpg']:
            self.card_ui(current)
        elif current == 'sprites':
            self.sprites_ui()
        elif current == 'bg-event':
            self.bg_event_ui()
        elif current == 'icon':
            self.icon_ui()
        elif current == 'sound':
            self.sound_ui()

    def card_ui(self, card_type: str):
        self.setFixedSize(380, 280)
        container = QWidget()
        layout_vertical = QVBoxLayout(container)

        # Star Selection
        star_layout = QHBoxLayout()
        star_label = QLabel("Star Card:")
        self.star_combo = QComboBox()
        for star in sorted(card_star_id.keys(), key=lambda x: int(x)):
            self.star_combo.addItem(f"{star}★", star)
        # Default to Star 8
        self.star_combo.setCurrentIndex(7)
        star_layout.addWidget(star_label)
        star_layout.addWidget(self.star_combo)

        # Color Selection
        color_layout = QHBoxLayout()
        color_label = QLabel("Color:")
        self.color_combo = QComboBox()
        self.color_combo.addItem("All Colors", "all")
        for cid, cname in card_color_id.items():
            self.color_combo.addItem(f"{cname.capitalize()}", cid)
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_combo)

        # 5 digit number range
        range_layout = QHBoxLayout()
        range_layout.setAlignment(Qt.AlignLeft)
        instruction = QLabel("Input 5 digit number:")
        start_input = QLineEdit("14540")
        start_input.setFixedWidth(60)
        to_label = QLabel("to")
        end_input = QLineEdit("14600")
        end_input.setFixedWidth(60)

        range_layout.addWidget(instruction)
        range_layout.addWidget(start_input)
        range_layout.addWidget(to_label)
        range_layout.addWidget(end_input)

        download_button = QPushButton("DOWNLOAD")
        download_button.clicked.connect(
            lambda: self.download_card_asset(
                container,
                card_type,
                self.star_combo.currentData(),
                self.color_combo.currentData(),
                int(start_input.text()),
                int(end_input.text())
            )
        )

        layout_vertical.addLayout(star_layout)
        layout_vertical.addLayout(color_layout)
        layout_vertical.addLayout(range_layout)
        layout_vertical.addWidget(download_button)

        self.layout.addWidget(container)
        self._dynamic_widgets.append(container)

    def sprites_ui(self):
        self.setFixedSize(400, 250)
        container = QWidget()
        layout_vertical = QVBoxLayout(container)

        member_layout = QHBoxLayout()
        member_label = QLabel("Select Member:")
        self.member_combo = QComboBox()

        for mid, mname in self.member_data.items():
            self.member_combo.addItem(f"{mname}", mid)

        member_layout.addWidget(member_label)
        member_layout.addWidget(self.member_combo)

        download_button = QPushButton("DOWNLOAD")
        download_button.clicked.connect(
            lambda: self.download_sprites_asset(
                container,
                self.member_combo.currentData()
            )
        )

        layout_vertical.addLayout(member_layout)
        layout_vertical.addWidget(download_button)

        self.layout.addWidget(container)
        self._dynamic_widgets.append(container)

    def bg_event_ui(self):
        self.setFixedSize(400, 220)
        container = QWidget()
        layout_vertical = QVBoxLayout(container)

        event_layout = QHBoxLayout()
        event_label = QLabel("Event number (min 48):")
        event_input = QLineEdit("48")
        event_input.setFixedWidth(50)
        generation_label = QLabel("Generation:")
        self.generation_combo = QComboBox()
        self.generation_combo.addItem("All generation", "all")
        self.generation_combo.addItem("1 dan 2", "1 dan 2")
        for i in range(3,7):
            self.generation_combo.addItem(f"{i}", i)
        event_layout.addWidget(event_label)
        event_layout.addWidget(event_input)
        event_layout.addWidget(generation_label)
        event_layout.addWidget(self.generation_combo)

        download_button = QPushButton("DOWNLOAD")
        download_button.clicked.connect(
            lambda: self.download_bg_event_asset(
                container,
                int(event_input.text()),
                str(self.generation_combo.currentData())
            )
        )

        layout_vertical.addLayout(event_layout)
        layout_vertical.addWidget(download_button)

        self.layout.addWidget(container)
        self._dynamic_widgets.append(container)

    def icon_ui(self):
        self.setFixedSize(400, 220)
        container = QWidget()
        layout_vertical = QVBoxLayout(container)

        type_layout = QHBoxLayout()
        type_label = QLabel("Icon Type:")
        self.icon_type_combo = QComboBox()
        self.icon_type_combo.addItem("Normal", "normal_v8")
        self.icon_type_combo.addItem("Plain Winter", "plain_winter_v8")
        self.icon_type_combo.addItem("Both", "both")
        self.generation_icon_combo = QComboBox()
        self.generation_icon_combo.addItem("All generation", "all")
        self.generation_icon_combo.addItem("1 dan 2", "1 dan 2")
        for gen in range(3,7):
            self.generation_icon_combo.addItem(f"{gen}", gen)
        gen_icon_label = QLabel("Generation:")
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.icon_type_combo)
        type_layout.addWidget(gen_icon_label)
        type_layout.addWidget(self.generation_icon_combo)
        download_button = QPushButton("DOWNLOAD")
        download_button.clicked.connect(
            lambda: self.download_icon_asset(
                container,
                self.icon_type_combo.currentData(),
                str(self.generation_icon_combo.currentData())
            )
        )

        layout_vertical.addLayout(type_layout)
        layout_vertical.addWidget(download_button)

        self.layout.addWidget(container)
        self._dynamic_widgets.append(container)

    def sound_ui(self):
        self.setFixedSize(400, 250)
        container = QWidget()
        layout_vertical = QVBoxLayout(container)

        member_layout = QHBoxLayout()
        member_label = QLabel("Select Member:")
        self.sound_member_combo = QComboBox()
        for mid, mname in self.member_data.items():
            self.sound_member_combo.addItem(f"{mname}", mid)
        member_layout.addWidget(member_label)
        member_layout.addWidget(self.sound_member_combo)

        download_button = QPushButton("DOWNLOAD")
        download_button.clicked.connect(
            lambda: self.download_sound_asset(
                container,
                self.sound_member_combo.currentData()
            )
        )
        layout_vertical.addLayout(member_layout)
        layout_vertical.addWidget(download_button)

        self.layout.addWidget(container)
        self._dynamic_widgets.append(container)

    # ── Download Methods ──────────────────────────────────────────

    def download_card_asset(self, parent_widget, card_type: str, star: str, color_option: str, start_id: int, last_id: int):
        server = self.server.currentText()
        server_url = MAIN_PATH[server]
        path_prefix = FILE_PATH[card_type]
        ext = "png" if card_type == "card-png" else "jpg"
        folder_type = "png" if card_type == "card-png" else "jpg"
        star_code = card_star_id[star]

        if color_option == "all":
            color_ids = list(card_color_id.keys())
        else:
            color_ids = [color_option]

        tasks = []
        for file_id in range(start_id, last_id + 1):
            five_digit = str(file_id).zfill(5)
            for cid in color_ids:
                filename = f"{cid}{star_code}{five_digit}.{ext}"
                url = f"{server_url}{path_prefix}{filename}"
                dest_path = os.path.join(OUTPUT_PATH, "card", folder_type, f"star_{star}", filename)
                tasks.append({
                    "url": url,
                    "dest_path": dest_path,
                    "filename": filename
                })

        dialog = DownloadProgress(tasks, card_type, parent=parent_widget)
        dialog.exec_()

    def download_sprites_asset(self, parent_widget, member_id: str):
        server = self.server.currentText()
        server_url = MAIN_PATH[server]
        path_prefix = FILE_PATH["sprites"]
        member_name = self.member_data.get(str(member_id), f"member_{member_id}")

        versions = get_member_versions(str(member_id))
        chars = ['a', 'b', 'c', 'd', 'e', 'f', 'g']

        tasks = []
        for num in range(1, 11):
            two_digit = str(num).zfill(2)
            for ver in versions:
                for ch in chars:
                    filename = f"n{member_id}_{two_digit}_v{ver}_{ch}.png"
                    url = f"{server_url}{path_prefix}{filename}"
                    dest_path = os.path.join(OUTPUT_PATH, "sprites", member_name, filename)
                    tasks.append({
                        "url": url,
                        "dest_path": dest_path,
                        "filename": filename
                    })

        dialog = DownloadProgress(tasks, "sprites", parent=parent_widget)
        dialog.exec_()

    def download_bg_event_asset(self, parent_widget, event_num: int, gen: str):
        server = self.server.currentText()
        server_url = MAIN_PATH[server]
        event_2digit = str(event_num).zfill(2)
        member_id = list(self.member_data.keys())
        generation = {
            '1 dan 2': member_id[:33],
            '3': member_id[33:45],
            '4': member_id[45:61],
            '5': member_id[61:72],
            '6': member_id[72:],
            'all': member_id
        }

        tasks = []
        member_list = generation[gen]
        for mid in member_list:
            filename = f"bg_main_back_{mid}.jpg"
            url = f"{server_url}{FILE_PATH['bg-event']}love50{event_2digit}/index/bg/top/{filename}"
            dest_path = os.path.join(OUTPUT_PATH, "bg-event", f"event-{event_num}", filename)
            tasks.append({
                "url": url,
                "dest_path": dest_path,
                "filename": filename
            })

        dialog = DownloadProgress(tasks, "bg-event", parent=parent_widget)
        dialog.exec_()

    def download_icon_asset(self, parent_widget, icon_type: str, gen_icon: str):
        server = self.server.currentText()
        server_url = MAIN_PATH[server]
        base_path = FILE_PATH["icon"]
        member_id = list(self.member_data.keys())
        generation = {
            '1 dan 2': member_id[:33],
            '3': member_id[33:45],
            '4': member_id[45:61],
            '5': member_id[61:72],
            '6': member_id[72:],
            'all': member_id
        }

        if icon_type == "both":
            icon_types = ["normal_v8", "plain_winter_v8"]
        else:
            icon_types = [icon_type]
        tasks = []
        for itype in icon_types:
            for mid in generation[gen_icon]:
                filename = f"{mid}.png"
                url = f"{server_url}{base_path}{itype}/{filename}"
                dest_path = os.path.join(OUTPUT_PATH, "icon", itype, filename)
                tasks.append({
                    "url": url,
                    "dest_path": dest_path,
                    "filename": f"{itype}_{filename}"
                })

        dialog = DownloadProgress(tasks, "icon", parent=parent_widget)
        dialog.exec_()

    def download_sound_asset(self, parent_widget, member_id: str):
        server = self.server.currentText()
        server_url = MAIN_PATH[server]
        base_path = FILE_PATH["sound"]
        member_name = self.member_data.get(str(member_id), f"member_{member_id}")

        tasks = []

        # nogikoi_{member_id}.m4a
        nk_filename = f"nogikoi_{member_id}.m4a"
        nk_url = f"{server_url}{base_path}{nk_filename}"
        nk_dest = os.path.join(OUTPUT_PATH, "sound", member_name, nk_filename)
        tasks.append({
            "url": nk_url,
            "dest_path": nk_dest,
            "filename": nk_filename,
            "convert_wav": True
        })

        # nv_rehearsal_{member_id}_01 ~ _04.m4a
        for num in range(1, 5):
            nr_filename = f"nv_rehearsal_{member_id}_{str(num).zfill(2)}.m4a"
            nr_url = f"{server_url}{base_path}{nr_filename}"
            nr_dest = os.path.join(OUTPUT_PATH, "sound", member_name, nr_filename)
            tasks.append({
                "url": nr_url,
                "dest_path": nr_dest,
                "filename": nr_filename,
                "convert_wav": True
            })

        dialog = DownloadProgress(tasks, "sound", parent=parent_widget)
        dialog.exec_()

    @staticmethod
    def resource_path(relative_path):
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, relative_path)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
