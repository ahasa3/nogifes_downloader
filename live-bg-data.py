import shutil
from function import *
from usme_extract import cpk_extractor, usm_extractor, acb_extractor
start = 38001
end = 38009
last = 1

#code rumus = singleTh+1 00 urut
# contoh single kokoniwa nai mono (36th single) = 37001

def demux_video(path_extracted, KEY, output_path, filename):
    try:
        usm_path = f'{path_extracted}/movie'
        acb_path = f'{path_extracted}/music'
        usm_extractor(usm_path, KEY, path_extracted)
        acb_extractor(acb_path, KEY, path_extracted)
        video = f'{path_extracted}/movie.264_med'
        audio = f'{path_extracted}/0.wav'
        output = f'{output_path}/{filename}.mp4'
        merge_video_audio(video, audio, output)
        shutil.rmtree(path_extracted)
    except:
        print("gagal demux")

def image_background(path_asal, output_path, filename):
    output = f'{output_path}/{filename}.png'
    shutil.copy(f'{path_asal}/background', output)
    shutil.rmtree(path_asal)

download_path = f"{base_dir}/Downloads/live-background-data"
os.makedirs(download_path,exist_ok=True)
while start <= end:
    target = f'{start}{last}'
    nol = ""
    for i in range(8-len(target)):
        nol += "0"
    id_video = nol + str(target)

    filename = f'live_bg_data_{id_video}.cpk'
    link = f'{MAIN_PATH}{OPTIONAL_PATH["live-background-data"]}{filename}'
    response = requests.get(link, stream=True)

    if not os.path.exists(filename):
        download(response, filename)
        if response.status_code != 200:
            last+=1
            if last > 2:
                last = 1
                start+=1
            continue
    output_path = f'{download_path}/{filename[:-5]}'
    os.makedirs(output_path, exist_ok=True)
    if os.path.exists(f'{output_path}/{filename[:-4]}.mp4') or os.path.exists(f'{output_path}/{filename[:-4]}.png'):
        print(f'{filename[:-4]} Already Exists')
        last+=1
        if last > 2:
            last = 1
            start+=1
        continue
    print("demuxing...")
    path_raw = os.path.join(temp,filename)
    cpk_extractor(path_raw, KEY, download_path)
    path_extracted = path_raw[:-4]
    if last == 1:
        demux_video(path_extracted, KEY, output_path,filename[:-4])
    elif last == 2:
        image_background(path_extracted, output_path, filename[:-4])
    last+=1
    if last > 2:
        last = 1
        start+=1

    os.remove(path_raw)
    print(f'{filename} downloaded')