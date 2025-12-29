from function import *
from usme_extract import usm_extractor
import os

start = 2939
end = 3000
#reward_movie_02937
download_path = f"{base_dir}/Downloads/reward-movie"
os.makedirs(download_path,exist_ok=True)

for id_file in range(start, end+1):
    nol = ''
    if len(str(id_file)) < 5:
        for i in range(5-len(str(id_file))):
            nol+='0'
    video_id = nol+str(id_file)
    filename = f"reward_movie_{video_id}.usme"
    link = f'{MAIN_PATH}{OPTIONAL_PATH["reward-movie"]}{filename}'
    response = requests.get(link, stream=True)
    
    output_path = os.path.join(download_path, f'{filename[:-4]}mp4')
    if os.path.exists(output_path):
        print(f'{filename[:-5]} already exist')
        continue
    if response.status_code != 200:
        print(f'{filename[:-5]} not in the server')
        continue
    if not os.path.exists(f'/temp/{filename}'):
        download(response, filename)

    print('demuxing...')
    path_raw = os.path.join(base_dir,temp,filename)
    usm_extractor(path_raw, KEY, f'{base_dir}/temp')
    reward_movie(filename[:-5], download_path)
    os.remove(path_raw)
    print(f'{filename} downloaded')
    