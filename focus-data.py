from main import *
from usme_extract import cpk_extractor
start = input("id start: ")
end = input("id end: ")

for target in range(int(start), int(end)+1):
    nol = ""
    for i in range(5-len(str(target))):
        nol += "0"
    id_video = nol + str(target)
    filename = f'focus_data_{id_video}.cpk'
    link = f'{MAIN_PATH}{OPTIONAL_PATH["focus-data"]}{filename}'
    response = requests.get(link, stream=True)
    download(response, filename)
    print("demuxing...")
    path_raw = os.path.join(temp,filename)
    cpk_extractor(path_raw, KEY)
    merge2mp4(filename[:-5])
    os.remove(path_raw)
    print(f'{filename} downloaded')