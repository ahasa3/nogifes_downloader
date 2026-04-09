import sys, requests, os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel, QFileDialog, QMenuBar, QMenu,
    QAction, QAbstractItemView, QSlider, QFrame, QComboBox, QLineEdit, QDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from urllib.parse import urlparse

content_option = [
    'card voice',
    'focus data low',
    'focus data high',
    'live background data low',
    'live background data high',
    'live finish movie',
    'member standing',
    'movie card',
    'movie card with music',
    'other data low',
    'other data high',
    'photo common',
    'preview gacha',
    'reward movie',
    'unit gacha movie'
]

MAIN_PATH= {
    "server 1":"https://v1static.nogifes.jp/resource",
    "server 2":"https://v2static.nogifes.jp/resource"}
FILE_PATH = {"focus data low":"/Movie/Focus/",
            "focus-data-high":"/Movie/HighFocusMovie/",
            "live-finish-movie":"/Movie/LiveFinishMovie/",
            "live-background-data":"/Movie/LiveBg/",
            "live-background-data-high":"/Movie/HighLiveBg/",
            "other-data":"/Movie/Other/",
            "other-data-high":"/Movie/HighOtherMovie/",
            "movie-card":"/Movie/MovieCard/",
            "member-standing":"/Movie/Member/",
            "reward-movie":"/Movie/Reward/",
            "preview-gacha":"/Movie/Gacha/Preview/",
            "unit-gacha-movie":"/Movie/UnitGachaMovie/",
            "photo-common":"/Background/Photo/",
            "card":"/Android_2017_4_1f1/card/",
            "card-voice":"/Sound/CardVoice/"}
BASEDIR = os.path.dirname(os.path.abspath(__file__))
TEMP = os.path.join(BASEDIR, 'temp')
os.makedirs(TEMP,exist_ok= True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Nogifes Downloader")
        self.setGeometry(100, 100, 800, 600)

        self.window = QWidget()
        self.layout = QVBoxLayout()

        self.server = QComboBox()
        self.server.addItems(['server 1', 'server 2'])
        self.option = QComboBox()
        self.option.addItems(content_option)
        self.option.currentTextChanged.connect(self.option_select)
        
        self.setCentralWidget(self.window)
        self.window.setLayout(self.layout)
        self.layout.addWidget(self.server)
        self.layout.addWidget(self.option)

        self._dynamic_widgets = []

    def _clear_dynamic_widgets(self):
        for widget in self._dynamic_widgets:
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self._dynamic_widgets.clear()

    def option_select(self):
        self._clear_dynamic_widgets()

        if self.option.currentText() == "focus data low" or self.option.currentText() == 'focus data high':
            self.focus_data_ui()

    def focus_data_ui(self):
        container = QWidget()
        focus_layout_vertical = QVBoxLayout(container)
        focus_layout_horizontal = QHBoxLayout()
        intruction = QLabel("Input video id with 5 digit number:")
        start = QLineEdit("00001")
        end = QLineEdit("00010")
        download_button = QPushButton("Download")
        download_button.clicked.connect(
            lambda:self.download_asset(
                parent_widget=container,start_id = int(start.text()), last_id = int(end.text())
                ))
        focus_layout_horizontal.addWidget(intruction)
        focus_layout_horizontal.addWidget(start)
        focus_layout_horizontal.addWidget(end)

        focus_layout_vertical.addLayout(focus_layout_horizontal)
        focus_layout_vertical.addWidget(download_button)
        self.layout.addWidget(container)

        self._dynamic_widgets.append(container)

    def download_asset(self, parent_widget, start_id: int, last_id: int):
        urls = self.get_url(start_id=start_id,last_id=last_id)

        dialog = DownloadProgress(urls, parent=parent_widget)
        dialog.exec_()

    def get_url(self, start_id: int, last_id: int):
        option = self.option.currentText()
        server = self.server.currentText()
        files = []
        if self.option.currentText() == "focus data low":
            max_digit = 5
            files = [f'focus_data_{str(file_id).zfill(max_digit)}.cpk'
                        for file_id in range(start_id, last_id+1)]
        urls = [f'{MAIN_PATH[server]}{FILE_PATH[option]}{filename}'
               for filename in files]
        return urls

class Download(QThread):
    progress = pyqtSignal(str, int, int) # (filename, bytes_downloaded, total_bytes)
    file_done = pyqtSignal(str, bool, str) # (filelname, success, message)
    # ffmpeg_output = pyqtSignal(str, str) # (filename, line_output)
    # all_done = pyqtSignal()

    def __init__(self, files: list[str]):
        super().__init__()
        self.urls = files
    
    def run(self):
        for url in self.urls:
            filename = os.path.basename(urlparse(url).path)
            filepath = os.path.join(BASEDIR, TEMP, filename)
            try:
                response = requests.get(url, stream=True, timeout=30)
                if response.status_code == 200:
                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0

                    with open (filepath, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded+=len(chunk)
                                self.progress.emit(filename, downloaded, total_size)
                    self.file_done.emit(filename, True, "Downloaded")
                else:
                    self.file_done.emit(filename, False, "is not in the server")
                    continue
            except Exception as e:
                self.file_done.emit(filename, False, str(e))
                continue

class DownloadProgress(QDialog):
    def __init__(self, files: list[str], parent = None):
        super().__init__(parent)
        self.urls=files
        self.file_widgets = {}

        self._build_ui()
        self._start_download()
    
    def _build_ui(self):
        self.setWindowTitle("File Process")
        self.setMinimumWidth(550)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

        layout = QVBoxLayout(self)

        for url in self.urls:
            filename = os.path.basename(urlparse(url).path)

            lbl_name = QLabel(filename)
            lbl_name.setStyleSheet("font-weight: bold;")

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setFormat("%p% - Downloading...")

            lbl_status = QLabel("Downloading...")
            lbl_status.setStyleSheet("color: gray; font-size: 11px;")

            layout.addWidget(lbl_name)
            layout.addWidget(bar)
            layout.addWidget(lbl_status)

            self.file_widgets[filename] = {"bar":bar, "status":lbl_status}

            #ffmpeg

            #ffmpeg

    def _start_download(self):
        self.downloading = Download(self.urls)
        self.downloading.progress.connect(self._on_progress)
        self.downloading.file_done.connect(self._on_file_done)
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
        if success:
            w["bar"].setValue(100)
            w["bar"].setFormat("✅ 100%")
            w["status"].setText(message)
            w["status"].setStyleSheet("color: green;")
        else:
            w["bar"].setFormat("❌ Gagal")
            w["status"].setText(f"Error: {message}")
            w["status"].setStyleSheet("color: red;")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()