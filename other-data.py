import shutil
from function import *
from usme_extract import cpk_extractor, usm_extractor, acb_extractor

start = 100
end = 101
#other_data_00100.cpk
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
download_path = f"{base_dir}/Downloads/other-data"
os.makedirs(download_path,exist_ok=True)
for target in range(start, end):
    nol = 5-len(str(start))
    id_video = '0'*nol + str(target)

    filename = f'other_data_{id_video}.cpk'
    link = f'{MAIN_PATH}{OPTIONAL_PATH["other-data"]}{filename}'
    response = requests.get(link, stream=True)

    output_path = f'{download_path}/{filename[:-5]}'
    
    if os.path.exists(f'{output_path}/{filename[:-4]}.mp4') or os.path.exists(f'{output_path}/{filename[:-4]}.png'):
        print(f'{filename[:-4]} Already Exists')
        
        continue

    if not os.path.exists(filename):
        download(response, filename)
        if response.status_code != 200:
            print(f'{filename[:-4]} not in the server')
            continue
            
    os.makedirs(output_path, exist_ok=True)
    print("demuxing...")
    path_raw = os.path.join(temp,filename)
    cpk_extractor(path_raw, download_path)
    path_extracted = path_raw[:-4]
    demux_video(path_extracted, KEY, output_path,filename[:-4])

    os.remove(path_raw)
    print(f'{filename} downloaded')