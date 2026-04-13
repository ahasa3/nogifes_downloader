import sys, requests, os, subprocess, shutil, glob, builtins, inspect
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel, QFileDialog, QMenuBar, QMenu,
    QAction, QAbstractItemView, QSlider, QFrame, QComboBox, QLineEdit, QDialog, QProgressBar, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from urllib.parse import urlparse
from PyCriCodecs import ACB, AWB, CPK, USM

content_option = [
    'card voice',
    'focus data low',
    'focus data high',
    'live background data low',
    'live background data high',
    'live finish movie',
    'member standing',
    'movie card',
    # 'movie card with music',
    'other data low',
    'other data high',
    'photo common',
    # 'preview gacha',
    'reward movie',
    'unit gacha movie'
]

MAIN_PATH= {
    "server 1":"https://v1static.nogifes.jp/resource",
    "server 2":"https://v2static.nogifes.jp/resource"}
FILE_PATH = {"card voice":"/Sound/CardVoice/",
            "focus data low":"/Movie/Focus/",
            "focus data high":"/Movie/HighFocusMovie/",
            "live finish movie":"/Movie/LiveFinishMovie/",
            "live background data low":"/Movie/LiveBg/",
            "live background data high":"/Movie/HighLiveBg/",
            "other data low":"/Movie/Other/",
            "other data high":"/Movie/HighOtherMovie/",
            "movie card":"/Movie/MovieCard/",
            "member standing":"/Movie/Member/",
            "reward movie":"/Movie/Reward/",
            "preview gacha":"/Movie/Gacha/Preview/",
            "unit gacha movie":"/Movie/UnitGachaMovie/",
            "photo common":"/Background/Photo/"
            }

EXTRACT_KEY = 0x0013F11BC5510101
BASEDIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASEDIR, "Downloads")
TEMP = os.path.join(BASEDIR, 'temp')
os.makedirs(TEMP,exist_ok= True)
os.makedirs(OUTPUT_PATH, exist_ok=True)

class BaseProcessor:
    def __init__(self, worker):
        self.worker = worker
    
    def get_output_path(self, filename):
        return None
    
    def process(self, filepath, filename):
        raise NotImplementedError

class CardVoiceProcessor(BaseProcessor):
    def get_output_path(self, filename):
        return os.path.join(OUTPUT_PATH, "card-voice", filename[:-4])
    
    def process(self, filepath, filename):
        self.worker.extract.emit(filename)
        output_dir = os.path.join(OUTPUT_PATH, "card-voice", filename[:-4])
        os.makedirs(output_dir, exist_ok=True)

        try:
            extractor = Extractor()
            extractor.card_voice(filepath, output_dir)
            self.worker.extract_done.emit(filename, True, f"{filename[:-4]} Downloaded")
        except Exception as e:
            self.worker.extract_done.emit(filename, False, str(e))
            return
        
        self.worker.all_done.emit()

class FocusDataLowProcessor(BaseProcessor):
    def get_output_path(self, filename):
        return os.path.join(OUTPUT_PATH, "focus-data", filename.replace(".cpk", ".mp4"))
    
    def process(self, filepath, filename):
        self.worker.extract.emit(filename)
        extracted_path = filepath[:-4]
        
        try:
            extractor = Extractor()
            extractor.focus_data(filepath=filepath, extracted_path=extracted_path)
            self.worker.extract_done.emit(filename, True,  "CPK Extracted")
            os.remove(filepath)
        except Exception as e:
            self.worker.extract_done.emit(filename, False, str(e))
            return

        self.worker.ffmpeg_output.emit(filename, "converting")
        try:
            video_path = os.path.join(extracted_path, "movie.264_med")
            audio_path = os.path.join(extracted_path, "0.wav")

            ffmpeg = Ffmpeg_process(self.worker)
            ffmpeg.focus_data_low(filename, video_path, audio_path)
        except  Exception as e:
            self.worker.file_done.emit(filename, False, f"FFmpeg: {str(e)}")
        shutil.rmtree(extracted_path)
        self.worker.all_done.emit()

class FocusDataHighProcessor(BaseProcessor):
    def get_output_path(self, filename):
        return os.path.join(OUTPUT_PATH, "focus-data-high", filename.replace(".cpk", ".mp4"))
    
    def process(self, filepath, filename):
        self.worker.extract.emit(filename)
        extracted_path = filepath[:-4]
        
        try:
            extractor = Extractor()
            extractor.focus_data(filepath=filepath, extracted_path=extracted_path)
            self.worker.extract_done.emit(filename, True,  "CPK Extracted")
            os.remove(filepath)
        except Exception as e:
            self.worker.extract_done.emit(filename, False, str(e))
            return

        self.worker.ffmpeg_output.emit(filename, "converting")
        try:
            video_path = os.path.join(extracted_path, "movie.264_med")
            audio_path = os.path.join(extracted_path, "0.wav")

            ffmpeg = Ffmpeg_process(self.worker)
            ffmpeg.focus_data_high(filename, video_path, audio_path)
        except  Exception as e:
            self.worker.file_done.emit(filename, False, f"FFmpeg: {str(e)}")
        shutil.rmtree(extracted_path)
        self.worker.all_done.emit()

class LiveBackgroundDataLowProcessor(BaseProcessor):
    def get_output_path(self, filename):
        if filename[-5:-4] == "1":
            return os.path.join(OUTPUT_PATH, "live-background-data", filename[:-5], filename.replace(".cpk", ".mp4"))
        elif filename[-5:-4] == "2":
            return os.path.join(OUTPUT_PATH, "live-background-data", filename[:-5], filename.replace(".cpk", ".png"))
    
    def process(self, filepath, filename):
        self.worker.extract.emit(filename)
        extracted_path = filepath[:-4]

        try:
            extractor = Extractor()
            if int(filename[-5:-4]) == 1:
                extractor.focus_data(filepath=filepath, extracted_path=extracted_path) #process same as focus  data
            elif int(filename[-5:-4]) == 2:
                extractor.cpk_extractor(filepath)
            self.worker.extract_done.emit(filename, True,  "CPK Extracted")
            os.remove(filepath)
        except Exception as e:
            self.worker.extract_done.emit(filename, False, str(e))
            return

        self.worker.ffmpeg_output.emit(filename, "converting")
        try:
            if int(filename[-5:-4]) == 1:
                video_path = os.path.join(extracted_path, "movie.264_med")
                audio_path = os.path.join(extracted_path, "0.wav")

                ffmpeg = Ffmpeg_process(self.worker)
                ffmpeg.live_background_data(filename, video_path, audio_path)
            elif int(filename[-5:-4]) == 2:
                output = os.path.join(OUTPUT_PATH, "live-background-data", filename[:-5], filename.replace(".cpk", ".png"))
                shutil.copy(f'{extracted_path}/background', output)
            
            self.worker.file_done.emit(filename, True, f'{filename[:-4]} Downloaded')
        except  Exception as e:
            self.worker.file_done.emit(filename, False, f"FFmpeg: {str(e)}")
        shutil.rmtree(extracted_path)
        self.worker.all_done.emit()

class LiveBackgroundDataHighProcessor(BaseProcessor):
    def get_output_path(self, filename):
        return os.path.join(OUTPUT_PATH, "live-background-data", filename[:-5], filename.replace(".cpk", ".mp4"))
    
    def process(self, filepath, filename):
        self.worker.extract.emit(filename)
        extracted_path = filepath[:-4]

        try:
            extractor = Extractor()
            extractor.focus_data(filepath=filepath, extracted_path=extracted_path) #process same as focus data
            self.worker.extract_done.emit(filename, True,  "CPK Extracted")
            os.remove(filepath)
        except Exception as e:
            self.worker.extract_done.emit(filename, False, str(e))
            return

        self.worker.ffmpeg_output.emit(filename, "converting")
        try:
            video_path = os.path.join(extracted_path, "movie.264_med")
            audio_path = os.path.join(extracted_path, "0.wav")

            ffmpeg = Ffmpeg_process(self.worker)
            ffmpeg.live_background_data(filename, video_path, audio_path)
            
            self.worker.file_done.emit(filename, True, f'{filename[:-4]} Downloaded')
        except  Exception as e:
            self.worker.file_done.emit(filename, False, f"FFmpeg: {str(e)}")
        shutil.rmtree(extracted_path)
        self.worker.all_done.emit()

class LiveFinishMovieProcessor(BaseProcessor):
    def get_output_path(self, filename):
        return os.path.join(OUTPUT_PATH, 'live-finish-movie', filename.replace(".usme", ".mp4"))
    
    def process(self, filepath, filename):
        self.worker.extract.emit(filename)
        
        
        try:
            extractor = Extractor()
            extractor.usm_extractor(filepath, EXTRACT_KEY, TEMP)
            self.worker.extract_done.emit(filename, True,  "USME Extracted")
            os.remove(filepath)
        except Exception as e:
            self.worker.extract_done.emit(filename, False, str(e))
            return

        self.worker.ffmpeg_output.emit(filename, "converting")
        try:
            video_path = glob.glob(os.path.join(TEMP, "*.ivf"))[0]
            audio_path = glob.glob(os.path.join(TEMP, "*.sfa"))[0]

            ffmpeg = Ffmpeg_process(self.worker)
            
            ffmpeg.live_finish_movie(filename, video_path, audio_path)
            os.remove(video_path)
            os.remove(audio_path)

        except  Exception as e:
            self.worker.file_done.emit(filename, False, f"FFmpeg: {str(e)}")
        self.worker.all_done.emit()

class MemberStandingProcessor(BaseProcessor):
    def get_output_path(self, filename):
        return os.path.join(OUTPUT_PATH, "member-standing", filename.replace(".usme", ".mp4"))
    
    def process(self, filepath, filename):
        self.worker.extract.emit(filename)
        
        try:
            extractor = Extractor()
            extractor.usm_extractor(filepath, EXTRACT_KEY, TEMP)
            self.worker.extract_done.emit(filename, True,  "USME Extracted")
            os.remove(filepath)
        except Exception as e:
            self.worker.extract_done.emit(filename, False, str(e))
            return

        self.worker.ffmpeg_output.emit(filename, "converting")
        try:
            video_path = glob.glob(os.path.join(TEMP, "*.ivf"))[0]

            ffmpeg = Ffmpeg_process(self.worker)
            
            ffmpeg.member_standing(filename, video_path)
            os.remove(video_path)

        except  Exception as e:
            self.worker.file_done.emit(filename, False, f"FFmpeg: {str(e)}")
        self.worker.all_done.emit()

class MovieCardProcessor(BaseProcessor):
    def get_output_path(self, filename):
        return os.path.join(OUTPUT_PATH, "movie-card", filename.replace(".usme", ".mp4"))
    
    def process(self, filepath, filename):
        self.worker.extract.emit(filename)
        
        try:
            extractor = Extractor()
            extractor.usm_extractor(filepath, EXTRACT_KEY, TEMP)
            self.worker.extract_done.emit(filename, True,  "USME Extracted")
            os.remove(filepath)
        except Exception as e:
            self.worker.extract_done.emit(filename, False, str(e))
            return

        self.worker.ffmpeg_output.emit(filename, "converting")
        try:
            video_path = glob.glob(os.path.join(TEMP, "*.264_med"))[0]

            ffmpeg = Ffmpeg_process(self.worker)
            
            ffmpeg.movie_card(filename, video_path)
            os.remove(video_path)

        except  Exception as e:
            self.worker.file_done.emit(filename, False, f"FFmpeg: {str(e)}")
        self.worker.all_done.emit()

class OtherDataLowProcessor(BaseProcessor):
    def get_output_path(self, filename):
        return os.path.join(OUTPUT_PATH, "other-data", filename.replace(".cpk", ".mp4"))
    
    def process(self, filepath, filename):
        self.worker.extract.emit(filename)
        extracted_path = filepath[:-4]
        
        try:
            extractor = Extractor()
            extractor.focus_data(filepath=filepath, extracted_path=extracted_path) #process same as focus data
            self.worker.extract_done.emit(filename, True,  "CPK Extracted")
            os.remove(filepath)
        except Exception as e:
            self.worker.extract_done.emit(filename, False, str(e))
            return

        self.worker.ffmpeg_output.emit(filename, "converting")
        try:
            video_path = os.path.join(extracted_path, "movie.264_med")
            audio_path = os.path.join(extracted_path, "0.wav")

            ffmpeg = Ffmpeg_process(self.worker)
            ffmpeg.other_data_low(filename, video_path, audio_path)
        except  Exception as e:
            self.worker.file_done.emit(filename, False, f"FFmpeg: {str(e)}")
        shutil.rmtree(extracted_path)
        self.worker.all_done.emit()

class OtherDataHighProcessor(BaseProcessor):
    def get_output_path(self, filename):
        return os.path.join(OUTPUT_PATH, "other-data-high", filename.replace(".cpk", ".mp4"))
    
    def process(self, filepath, filename):
        self.worker.extract.emit(filename)
        extracted_path = filepath[:-4]
        
        try:
            extractor = Extractor()
            extractor.focus_data(filepath=filepath, extracted_path=extracted_path) #process same as focus data
            self.worker.extract_done.emit(filename, True,  "CPK Extracted")
            os.remove(filepath)
        except Exception as e:
            self.worker.extract_done.emit(filename, False, str(e))
            return

        self.worker.ffmpeg_output.emit(filename, "converting")
        try:
            video_path = os.path.join(extracted_path, "movie.264_med")
            audio_path = os.path.join(extracted_path, "0.wav")

            ffmpeg = Ffmpeg_process(self.worker)
            ffmpeg.other_data_high(filename, video_path, audio_path)
        except  Exception as e:
            self.worker.file_done.emit(filename, False, f"FFmpeg: {str(e)}")
        shutil.rmtree(extracted_path)
        self.worker.all_done.emit()

class PhotoCommonProcessor(BaseProcessor):
    def get_output_path(self, filename):
        return os.path.join(OUTPUT_PATH, "photo-common", filename)
    
    def process(self, filepath, filename):
        shutil.move(filepath, os.path.join(OUTPUT_PATH, "photo-common", filename))
        self.worker.all_done.emit()

class RewardMovieProcessor(BaseProcessor):
    def get_output_path(self, filename):
        return os.path.join(OUTPUT_PATH, 'reward-movie', filename.replace(".usme", ".mp4"))
    
    def process(self, filepath, filename):
        self.worker.extract.emit(filename)
        
        try:
            extractor = Extractor()
            extractor.usm_extractor(filepath, EXTRACT_KEY, TEMP)
            self.worker.extract_done.emit(filename, True,  "USME Extracted")
            os.remove(filepath)
        except Exception as e:
            self.worker.extract_done.emit(filename, False, str(e))
            return

        self.worker.ffmpeg_output.emit(filename, "converting")
        try:
            video_path = glob.glob(os.path.join(TEMP, "*.264_med"))[0]
            audio_path = glob.glob(os.path.join(TEMP, "*.avi"))[0]

            ffmpeg = Ffmpeg_process(self.worker)
            
            ffmpeg.reward_movie(filename, video_path, audio_path)
            os.remove(video_path)
            os.remove(audio_path)

        except  Exception as e:
            self.worker.file_done.emit(filename, False, f"FFmpeg: {str(e)}")
        self.worker.all_done.emit()

class UnitGachaMovieProcessor(BaseProcessor):
    def get_output_path(self, filename):
        return os.path.join(OUTPUT_PATH, "unit-gacha-movie", filename.replace(".usme", ".mp4"))
    
    def process(self, filepath, filename):
        self.worker.extract.emit(filename)
        
        try:
            extractor = Extractor()
            extractor.usm_extractor(filepath, EXTRACT_KEY, TEMP)
            self.worker.extract_done.emit(filename, True,  "USME Extracted")
            os.remove(filepath)
        except Exception as e:
            self.worker.extract_done.emit(filename, False, str(e))
            return

        self.worker.ffmpeg_output.emit(filename, "converting")
        try:
            video_path = glob.glob(os.path.join(TEMP, "*.ivf"))[0]

            ffmpeg = Ffmpeg_process(self.worker)
            
            ffmpeg.unit_gacha_movie(filename, video_path)
            os.remove(video_path)

        except  Exception as e:
            self.worker.file_done.emit(filename, False, f"FFmpeg: {str(e)}")
        self.worker.all_done.emit()

class DefaultProcessor(BaseProcessor):
    def process(self, filepath, filename):
        self.worker.extract_done.emit(filename, True, "No Process Needed")

PROCESSOR_MAP = {
    "card voice": CardVoiceProcessor,
    "focus data low": FocusDataLowProcessor,
    "focus data high": FocusDataHighProcessor,
    "live background data low": LiveBackgroundDataLowProcessor,
    "live background data high": LiveBackgroundDataHighProcessor,
    "live finish movie": LiveFinishMovieProcessor,
    "member standing": MemberStandingProcessor,
    "movie card": MovieCardProcessor,
    "other data low": OtherDataLowProcessor,
    "other data high": OtherDataHighProcessor,
    "photo common": PhotoCommonProcessor,
    "reward movie": RewardMovieProcessor,
    "unit gacha movie": UnitGachaMovieProcessor
}

class Progress(QThread):
    start_progress = pyqtSignal(str) # (filename)
    progress = pyqtSignal(str, int, int) # (filename, bytes_downloaded, total_bytes)
    file_done = pyqtSignal(str, bool, str) # (filename, success, message)
    extract = pyqtSignal(str)
    extract_done = pyqtSignal(str, bool, str)
    ffmpeg_output = pyqtSignal(str, str) # (filename, line_output)
    all_done = pyqtSignal()

    def __init__(self, urls, option):
        super().__init__()
        self.urls = urls
        self.option = option
    
    def run(self):
        for url in self.urls:
            filename = os.path.basename(urlparse(url).path)
            filepath = os.path.join(BASEDIR, TEMP, filename)

            processor_class = PROCESSOR_MAP.get(self.option, DefaultProcessor)
            processor = processor_class(self)

            output_path = processor.get_output_path(filename)
            if output_path and os.path.exists(output_path):
                self.start_progress.emit(filename)
                self.file_done.emit(filename, True, f'{filename[:-4]} already exist')
                continue

            self.start_progress.emit(filename)

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
                    self.file_done.emit(filename, True, f"{filename} Downloaded")
                else:
                    self.file_done.emit(filename, False, "is not in the server")
                    continue
            except Exception as e:
                self.file_done.emit(filename, False, str(e))
                continue

            processor.process(filepath, filename)

class DownloadProgress(QDialog):
    def __init__(self, urls, option, parent = None):
        super().__init__(parent)
        self.urls=urls
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
        lbl = QLabel(filename[:-4])
        bar = QProgressBar()
        status = QLabel("Downloading...")

        self.download_layout.insertWidget(self.download_layout.count()-1, lbl)
        self.download_layout.insertWidget(self.download_layout.count()-1, bar)
        self.download_layout.insertWidget(self.download_layout.count()-1, status)

        self.file_widgets[filename] = {
            "label":lbl,
            "bar": bar,
            "status": status
        }

        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    def _start_download(self):
        self.downloading = Progress(self.urls, self.option)
        self.downloading.start_progress.connect(self._add_file_widget)
        self.downloading.progress.connect(self._on_progress)
        self.downloading.file_done.connect(self._on_file_done)
        self.downloading.extract.connect(self._on_extract_start)
        self.downloading.extract_done.connect(self._on_extract_done)
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
            w["label"].setText(f'{filename[:-4]} already exist')
            w["label"].setStyleSheet("color: green;")
            w["status"].hide()
        if "is not in the server" in message:
            w["bar"].hide()
            w["label"].setText(f'{filename} is not in the server')
            w["label"].setStyleSheet("color: red;")
            w["status"].hide()
        if success:
            w["bar"].setValue(100)
            w["bar"].setFormat("✅ 100%")
            w["status"].setText(message)
            w["status"].setStyleSheet("color: green;")
        else:
            w["bar"].setFormat("❌ Gagal")
            w["status"].setText(f"Error: {message}")
            w["status"].setStyleSheet("color: red;")

    def _on_extract_start(self, filename):
        w = self.file_widgets.get(filename)
        if not w:
            return

        w["bar"].setValue(0)
        w["bar"].setFormat("Extracting...")
        w["status"].setText("📦 Extracting...")
        w["status"].setStyleSheet("color: orange;")

    def _on_extract_done(self, filename, success, message):
        w = self.file_widgets.get(filename)
        if not w:
            return

        if success:
            w["bar"].setValue(100)
            w["bar"].setFormat("📦 Done")
            w["status"].setText(message)
            w["status"].setStyleSheet("color: green;")
        else:
            w["bar"].setFormat("❌ Extract Failed")
            w["status"].setText(f"Error: {message}")
            w["status"].setStyleSheet("color: red;")
    def _on_ffmpeg_output(self, filename:str, line:str):
        self.log_box.append(f"[{filename}] {line}")

        self.log_box.verticalScrollBar().setValue(
            self.log_box.verticalScrollBar().maximum()
        )
    
    def _on_all_done(self):
        self.btn_close.setEnabled(True)
        self.setWindowFlag(Qt.WindowCloseButtonHint, True)
        self.show()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Nogifes Downloader")
        self.setMinimumSize(400,200)

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

        if self.option.currentText() == "card voice" or \
                self.option.currentText() == "live finish movie" or \
                self.option.currentText() == "unit gacha movie":
            self.form_default_ui(
                "Input video id with 6 digit number:",
                "009227",
                "009229"
            )
        if self.option.currentText() == "focus data low" or \
                self.option.currentText() == 'focus data high' or \
                self.option.currentText() == 'movie card' or \
                self.option.currentText() == 'other data low' or \
                self.option.currentText() == 'other data high' or \
                self.option.currentText() == 'reward movie':
            self.form_default_ui(
                "Input video id with 5 digit number:",
                "00001",
                "00002"
            )
        if self.option.currentText() == "live background data low" or self.option.currentText() == "live background data high":
            self.live_bg_ui()
        
        if self.option.currentText() == "member standing":
            self.member_standing_ui()

        if self.option.currentText() == "photo common":
            self.form_default_ui(
                "Input photo id with 5 digit",
                "00001",
                "00002"
            )
        

    def form_default_ui(self, intruction_label, start_default, end_default):
        self.setFixedHeight(200)
        container = QWidget()
        layout_vertical = QVBoxLayout(container)
        layout_horizontal = QHBoxLayout()
        intruction = QLabel(intruction_label)
        start = QLineEdit(start_default)
        to = QLabel("to")
        end = QLineEdit(end_default)
        download_button = QPushButton("DOWNLOAD")
        download_button.clicked.connect(
            lambda:self.download_asset(
                parent_widget=container,start_id = int(start.text()), last_id = int(end.text())
                ))
        layout_horizontal.addWidget(intruction)
        layout_horizontal.addWidget(start)
        layout_horizontal.addWidget(to)
        layout_horizontal.addWidget(end)

        layout_vertical.addLayout(layout_horizontal)
        layout_vertical.addWidget(download_button)
        self.layout.addWidget(container)

        self._dynamic_widgets.append(container)
    
    def live_bg_ui(self):
        self.setFixedHeight(450)
        container = QWidget()
        layout_vertical = QVBoxLayout(container)
        layout_horizontal = QHBoxLayout()
        album = "Single ID for each Album:\n\n" \
        "11 = 1st Album\n\n" \
        "16 = 2nd album\n\n" \
        "20 = 3rd album\n\n" \
        "23 = under super best\n\n" \
        "27 = 4th album\n\n" \
        "34 = album time flies\n\n"

        user_help = "Single ID = Single number + number of singles\n\n" \
        "example: I want to download 36Th single.\n\n" \
        "single id = 36 (single number) + 6 (number of single before) = 42"

        list_album = QLabel(album)
        input_help = QLabel(user_help)
        intruction = QLabel("Input 2 digit Single ID")
        start = QLineEdit("01")
        to = QLabel("to")
        end = QLineEdit("02")
        download_button = QPushButton("DOWNLOAD")
        download_button.clicked.connect(
            lambda:self.download_asset(
                parent_widget=container,start_id = int(start.text()), last_id = int(end.text())
                ))
        layout_horizontal.addWidget(intruction)
        layout_horizontal.addWidget(start)
        layout_horizontal.addWidget(to)
        layout_horizontal.addWidget(end)

        layout_vertical.addWidget(list_album)
        layout_vertical.addWidget(input_help)
        layout_vertical.addLayout(layout_horizontal)
        layout_vertical.addWidget(download_button)
        self.layout.addWidget(container)

        self._dynamic_widgets.append(container)
    
    def member_standing_ui(self):
        self.setFixedHeight(200)
        container = QWidget()
        layout_vertical = QVBoxLayout(container)
        layout_horizontal = QHBoxLayout()
        intruction = QLabel("Download for")
        start = QLineEdit("1")
        to = QLabel("kisei")
        download_button = QPushButton("DOWNLOAD")
        download_button.clicked.connect(
            lambda:self.download_asset(
                parent_widget=container,start_id = int(start.text()), last_id = 1
                ))
        layout_horizontal.addWidget(intruction)
        layout_horizontal.addWidget(start)
        layout_horizontal.addWidget(to)

        layout_vertical.addLayout(layout_horizontal)
        layout_vertical.addWidget(download_button)
        self.layout.addWidget(container)

        self._dynamic_widgets.append(container)

    def get_url(self, start_id: int, last_id: int):
        option = self.option.currentText()
        server = self.server.currentText()
        files = []

        if self.option.currentText() == "card voice":
            max_digit = 6
            files = [f'card_voice_{str(file_id).zfill(max_digit)}0.acb'
                     for file_id in range(start_id, last_id+1)]
        elif self.option.currentText() == "live finish movie":
            max_digit = 6
            files = [f'live_finish_movie_{str(file_id).zfill(max_digit)}0.usme'
                     for file_id in range(start_id, last_id+1)]
        elif self.option.currentText() == "unit gacha movie":
            max_digit = 6
            files = [f'unit_gacha_movie_{str(file_id).zfill(max_digit)}0.usme'
                     for file_id in range(start_id, last_id+1)]
            
        if self.option.currentText() == "focus data low":
            max_digit = 5
            files = [f'focus_data_{str(file_id).zfill(max_digit)}.cpk'
                        for file_id in range(start_id, last_id+1)]
        elif self.option.currentText() == "focus data high":
            max_digit = 5
            files = [f'focus_data_high_{str(file_id).zfill(max_digit)}.cpk'
                        for file_id in range(start_id, last_id+1)]
        
        if self.option.currentText() == "live background data low":
            files = []
            for single_id in range(start_id,last_id+1):
                for music_id in range(1,13): # 12 song
                    for music_last_id in  range(1,3): # 1 for video, 2 for image
                        files.append(f'live_bg_data_00{single_id}0{str(music_id).zfill(2)}{music_last_id}.cpk')
        elif self.option.currentText() == "live background data high":
            files = []
            for single_id in range(start_id,last_id+1):
                for music_id in range(1,13): # 12 song
                        files.append(f'live_bg_data_00{single_id}0{str(music_id).zfill(2)}3.cpk')
        
        if self.option.currentText() == "member standing":
            if start_id == 1:
                files = [
                    f'member_standing_movie_0{start_id}{str(member_id).zfill(2)}.usme'
                    for member_id in range(last_id, 23)
                ]
            else:
                files = [
                    f'member_standing_movie_0{start_id}{str(member_id).zfill(2)}.usme'
                    for member_id in range(last_id, 17)
                ]

        if self.option.currentText() == "movie card":
            max_digit = 5
            files = [
                f'movie_card_{str(file_id).zfill(max_digit)}.usme'
                        for file_id in range(start_id, last_id+1)
            ]

        if self.option.currentText() == "other data low":
            max_digit = 5
            files = [
                f'other_data_{str(file_id).zfill(max_digit)}.cpk'
                        for file_id in range(start_id, last_id+1)
            ]
        elif self.option.currentText() == "other data high":
            max_digit = 5
            files = [
                f'other_data_high_{str(file_id).zfill(max_digit)}.cpk'
                        for file_id in range(start_id, last_id+1)
            ]

        if self.option.currentText() == "photo common":
            max_digit = 5
            files = [
                f'photo_common_{str(file_id).zfill(max_digit)}.png'
                        for file_id in range(start_id, last_id+1)
            ]

        if self.option.currentText() == "reward movie":
            max_digit = 5
            files = [
                f'reward_movie_{str(file_id).zfill(max_digit)}.usme'
                        for file_id in range(start_id, last_id+1)
            ]

        urls = [f'{MAIN_PATH[server]}{FILE_PATH[option]}{filename}'
               for filename in files]
        return urls

    def download_asset(self, parent_widget, start_id: int, last_id: int):
        urls = self.get_url(start_id=start_id,last_id=last_id)

        dialog = DownloadProgress(urls, self.option.currentText(), parent=parent_widget)
        dialog.exec_()

class Extractor():
    def __init__(self):
        self._real_open = builtins.open
        
    def safe_open(self, file, mode='r', *args, **kwargs):
        try:
            if isinstance(file, str) and "\\" in file:
                for frame in inspect.stack()[1:8]:
                    fname = frame.filename.replace("\\", "/")

                    if "PyCriCodecs/usm.py" in fname or fname.endswith("/usm.py"):
                        cleaned_basename = os.path.basename(file.replace("\\", "/"))
                        sanitized_path = os.path.join(TEMP, cleaned_basename)

                        return self._real_open(sanitized_path, mode, *args, **kwargs)

        except Exception as e:
            print("safe_open error:", e) 

        return self._real_open(file, mode, *args, **kwargs)

    def acb_extractor(self, filepath:str, key, output_file:str):
        acb = ACB(filepath)
        acb.extract(dirname=output_file, decode=True, key=key)
    
    def cpk_extractor(self, filepath: str):
        cpkObj = CPK(filepath)
        cpkObj.extract()
    
    def usm_extractor(self, filepath: str, key, output_dir: str):
        builtins.open = self.safe_open

        try:
            usm = USM(filepath, key=key)
            usm.extract(output_dir)
        finally:
            builtins.open = self._real_open
    
    def usm_extractor_for_focus_data(self, filepath: str, key, output_dir: str):
        usm = USM(filepath, key=key)
        usm.extract(output_dir)

    def card_voice(self, filepath, output_path):
        self.acb_extractor(filepath, EXTRACT_KEY, output_path)

    def focus_data(self, filepath, extracted_path):
        self.cpk_extractor(filepath)
        usm_path = os.path.join(extracted_path, "movie")
        acb_path = os.path.join(extracted_path, "music")
        self.acb_extractor(acb_path, EXTRACT_KEY, extracted_path)
        self.usm_extractor_for_focus_data(usm_path, EXTRACT_KEY, extracted_path)
    

class Ffmpeg_process():
    def __init__(self, worker):
        self.worker = worker

    def run_ffmpeg(self, filename, command):
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        output_lines = []
        for line in process.stdout:
            output_lines.append(line.strip())
            self.worker.ffmpeg_output.emit(filename, line.strip())

        process.wait()
        if process.returncode == 0:
            self.worker.file_done.emit(filename, True, f"{filename[:-4]} Downloaded")
        else:
        # Tampilkan semua output FFmpeg untuk debug
            full_output = "\n".join(output_lines[-10:])  # 10 baris terakhir
            self.worker.file_done.emit(filename, False, 
                f"FFmpeg error (code {process.returncode}):\n{full_output}")

    def focus_data_low(self, filename, video_path: str, audio_path: str):
        output_dir = os.path.join(OUTPUT_PATH, "focus-data")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename.replace(".cpk", ".mp4"))
        command = ["ffmpeg",
                   "-i", video_path,
                   "-i", audio_path,
                   "-c", "copy",
                   output_path,
                   "-y"]
        self.run_ffmpeg(filename, command)
    def focus_data_high(self, filename, video_path: str, audio_path: str):
        output_dir = os.path.join(OUTPUT_PATH, "focus-data-high")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename.replace(".cpk", ".mp4"))
        command = ["ffmpeg",
                   "-i", video_path,
                   "-i", audio_path,
                   "-c", "copy",
                   output_path,
                   "-y"]
        self.run_ffmpeg(filename, command)

    def live_background_data(self, filename, video_path, audio_path):
        output_dir = os.path.join(OUTPUT_PATH, "live-background-data", filename[:-5])
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename.replace(".cpk", ".mp4"))
        command = ["ffmpeg",
                   "-i", video_path,
                   "-i", audio_path,
                   "-c", "copy",
                   output_path,
                   "-y"]
        self.run_ffmpeg(filename, command)

    def live_finish_movie(self, filename, video_path, audio_path):
        output_dir = os.path.join(OUTPUT_PATH, "live-finish-movie")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename.replace(".usme", ".mp4"))
        command = ["ffmpeg",
                   "-i", video_path,
                   "-i", audio_path,
                   "-c:v", "copy",
                   "-c:a", "aac",
                   output_path,
                   "-y"]
        self.run_ffmpeg(filename, command)

    def member_standing(self, filename, video_path):
        output_dir = os.path.join(OUTPUT_PATH, "member-standing")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename.replace(".usme", ".mp4"))
        command = ["ffmpeg",
                   "-i", video_path,
                   "-c:v", "copy",
                   "-c:a", "aac",
                   output_path,
                   "-y"]
        self.run_ffmpeg(filename, command)

    def movie_card(self, filename, video_path):
        output_dir = os.path.join(OUTPUT_PATH, "movie-card")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename.replace(".usme", ".mp4"))
        command = ["ffmpeg",
                   "-i", video_path,
                   "-c:v", "copy",
                   "-c:a", "aac",
                   output_path,
                   "-y"]
        self.run_ffmpeg(filename, command)

    def other_data_low(self, filename, video_path, audio_path):
        output_dir = os.path.join(OUTPUT_PATH, "other-data")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename.replace(".cpk", ".mp4"))
        command = ["ffmpeg",
                   "-i", video_path,
                   "-i", audio_path,
                   "-c", "copy",
                   output_path,
                   "-y"]
        self.run_ffmpeg(filename, command)
    
    def other_data_high(self, filename, video_path, audio_path):
        output_dir = os.path.join(OUTPUT_PATH, "other-data-high")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename.replace(".cpk", ".mp4"))
        command = ["ffmpeg",
                   "-i", video_path,
                   "-i", audio_path,
                   "-c", "copy",
                   output_path,
                   "-y"]
        self.run_ffmpeg(filename, command)

    def reward_movie(self, filename, video_path, audio_path):
        output_dir = os.path.join(OUTPUT_PATH, "reward-movie")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename.replace(".usme", ".mp4"))
        command = ["ffmpeg",
                   "-i", video_path,
                   "-i", audio_path,
                   "-c:v", "copy",
                   "-c:a", "aac",
                   output_path,
                   "-y"]
        self.run_ffmpeg(filename, command)

    def unit_gacha_movie(self, filename, video_path):
        output_dir = os.path.join(OUTPUT_PATH, "unit-gacha-movie")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename.replace(".usme", ".mp4"))
        command = ["ffmpeg",
                   "-i", video_path,
                   "-c:v", "copy",
                   "-c:a", "aac",
                   output_path,
                   "-y"]
        self.run_ffmpeg(filename, command)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
    