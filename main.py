import requests, os, subprocess
from tqdm import tqdm

MAIN_PATH= "https://v2static.nogifes.jp/resource"
OPTIONAL_PATH = {"live-finish-movie":"/Movie/LiveFinishMovie/",
                 "focus-data":"/Movie/Focus/",
                 "live-background-data":"/Movie/LiveBg/",
                 "card-voice":"/Sound/CardVoice/"}
KEY = 0x0013F11BC5510101
#live_bg_data_00370032.cpk
base_dir = os.path.dirname(os.path.abspath(__file__))
temp = "temp"
os.makedirs(temp, exist_ok=True)
os.makedirs("Downloads", exist_ok=True)

def run_ffmpeg(cmd):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    for line in process.stdout:
        print(line, end="")

    process.wait()
    return process.returncode

def download(response, filename):
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))

        with open(os.path.join(base_dir, temp, filename), "wb") as f, tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=filename,
        ) as progress:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    progress.update(len(chunk))
        print("Download selesai:", filename)
    else:
        print("Gagal download, status:", response.status_code)

def merge2mp4(filename, path_output):
    path_merge = f"{base_dir}/temp/"
    try:
        ivf = os.path.join(path_merge, f"{filename}.ivf")
        sfa = os.path.join(path_merge, f"{filename}#00.sfa")
        out_mp4 = os.path.join(path_output, f"{filename}.mp4")
        print("merging...")
        run_ffmpeg([
            "ffmpeg", "-y",
            "-i", ivf,
            "-i", sfa,
            "-c:v", "copy",
            "-c:a", "aac",
            out_mp4
        ])
        os.remove(ivf)
        os.remove(sfa)
    except:
        filename = f'live_finish_movie_0{filename[-7:]}'
        ivf = os.path.join(path_merge, f"{filename}.ivf")
        sfa = os.path.join(path_merge, f"{filename}#00.sfa")
        out_mp4 = os.path.join(path_output, f"{filename}.mp4")
        print("merging...")
        run_ffmpeg([
            "ffmpeg", "-y",
            "-i", ivf,
            "-i", sfa,
            "-c:v", "copy",
            "-c:a", "aac",
            out_mp4
        ])
        os.remove(ivf)
        os.remove(sfa)
