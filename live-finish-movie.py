from function import *
from usme_extract import usm_extractor
live_finish = ['009227', '009228', '009229', 
               '009769', '009770', '009771', 
               '010055', '010056', '010057', 
               '010320', '010321', '010322', 
               '010617', '010618', '010619', 
               '011016', '011017', '011018', 
               '011277', '011278', '011279', 
               '011740', '011741', '011742', 
               '011850', '011851', '011852', 
               '012287', '012288', '012289', 
               '012420', '012421', '012422',
               '126020']
download_path = f"{base_dir}/Downloads/live-finish-movie"
os.makedirs(download_path,exist_ok=True)
server = int(input("choose server:\n1. server 1\n2. server 2\n\n"))
# for id_video in live_finish:
for id_video in range(12423,12900):
    filename = f"live_finish_movie_0{id_video}0.usme"
    if os.path.exists(f"{download_path}/{filename[:-5]}.mp4"):
        print(f'{filename[:-5]} already exist')
        continue
    link = f'{MAIN_PATH[server-1]}{OPTIONAL_PATH["live-finish-movie"]}{filename}'
    response = requests.get(link, stream=True)
    if response.status_code!=200:
        print(f'{filename} not in the server')
        continue
    download(response, filename)
    print("demuxing...")
    path_raw = os.path.join(base_dir,temp,filename)
    usm_extractor(path_raw, KEY, f'{base_dir}/temp')
    live_finish_movie(filename[:-5], download_path)
    os.remove(path_raw)
    print(f'{filename} downloaded')