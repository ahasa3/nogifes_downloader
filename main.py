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

def merge_video_audio(video, audio, output):
    if os.path.exists(output):
        print(f"{output} already exist")
    else:
        run_ffmpeg([
            "ffmpeg", "-y",
            "-i", video,
            "-i", audio,
            "-c:v", "copy",
            "-c:a", "aac",
            output
        ])
    os.remove(video)
    os.remove(audio)

def merge2mp4(filename, path_output):
    path_merge = f"{base_dir}/temp/"

    out_mp4 = os.path.join(path_output, f"{filename}.mp4")

    if os.path.exists(out_mp4):
        print(f"{filename}.mp4 already exist")
        return

    ivf = os.path.join(path_merge, f"{filename}.ivf")
    sfa = os.path.join(path_merge, f"{filename}#00.sfa")

    alt_filename = f'live_finish_movie_0{filename[-7:]}'
    alt_ivf = os.path.join(path_merge, f"{alt_filename}.ivf")
    alt_sfa = os.path.join(path_merge, f"{alt_filename}#00.sfa")

    print("merging...")

    if os.path.exists(ivf) and os.path.exists(sfa):
        merge_video_audio(ivf, sfa, out_mp4)
    elif os.path.exists(alt_ivf) and os.path.exists(alt_sfa):
        merge_video_audio(alt_ivf, alt_sfa, out_mp4)
    else:
        print(f"Source files for {filename} not found")

