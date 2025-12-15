import requests, os, subprocess
from tqdm import tqdm

MAIN_PATH= "https://v2static.nogifes.jp/resource"
OPTIONAL_PATH = {"live-finish-movie":"/Movie/LiveFinishMovie/",
                 "focus-data":"/Movie/Focus/",
                 "focus-data-high":"/Movie/HighFocusMovie/",
                 "live-background-data":"/Movie/LiveBg/",
                 "live-background-data-high":"/Movie/HighLiveBg/",
                 "other-data":"/Movie/Other/",
                 "card-voice":"/Sound/CardVoice/",
                 "member-standing":"/Movie/Member/",
                 "reward-movie":"/Movie/Reward/"}
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
        print(f'{filename} not in the server')

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

def member_standing(filename, path_output):
    path_merge = f'{base_dir}/temp/{filename}.ivf'
    output = f'{path_output}/{filename}.mp4'
    run_ffmpeg([
        "ffmpeg", "-y",
        "-i", path_merge,
        "-c:v", "copy",
        "-c:a", "aac",
        output
    ])
    os.remove(path_merge)
def live_finish_movie(filename, path_output):
    path_merge = f"{base_dir}/temp/"

    out_mp4 = os.path.join(path_output, f"{filename}.mp4")

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

def live_bg(filename, path_output):
    path_merge = f'{base_dir}/temp/{filename}'
    
    out_mp4 = os.path.join(path_output, f'{filename}.mp4')
    
    video = os.path.join(path_merge, 'movie')
    audio = os.path.join(path_merge, 'music')
    merge_video_audio(video, audio, out_mp4)

def reward_movie(filename, path_output):
    path_merge = os.path.join(base_dir, temp)

    output = os.path.join(path_output, f'{filename}.mp4')
    video = os.path.join(path_merge, f'{filename}.avi')
    run_ffmpeg([
        "ffmpeg", "-y",
        "-i", video,
        "-c:v", "copy",
        "-c:a", "aac",
        output
    ])