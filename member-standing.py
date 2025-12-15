from function import *
from usme_extract import usm_extractor

download_path = f"{base_dir}/Downloads/member-standing"
os.makedirs(download_path,exist_ok=True)

# gen = 1
# id_member = 1
# while gen <=6:
#     if len(str(id_member)) != 2:
#         video_id = f'0{id_member}'
#     else:
#         video_id = f'{id_member}'

#     filename = f'member_standing_movie_0{gen}{video_id}.usme'
#     link = f'{MAIN_PATH}{OPTIONAL_PATH['member-standing']}/{filename}'
#     if os.path.exists(f'{download_path}/{filename[:-5]}.mp4'):
#         print(f'{filename[:-5]} already exist')
#         id_member+=1
#         continue
#     response = requests.get(link, stream=True)
#     if response.status_code != 200:
#         id_member=1
#         continue
#     elif response != 200 and id_member <20:
#         gen+=1
#         id_member=1
#         continue
#     path_raw = os.path.join(base_dir, temp, filename)
#     if not os.path.exists(path_raw):
#         download(response,filename)

#     print('demuxing...')
#     usm_extractor(path_raw,KEY,f'{base_dir}/temp')
#     member_standing(filename[:-5], download_path)
#     id_member+=1
#     os.remove(path_raw)
#     print(f'{filename[:-5]} downloaded')

for gen in range(1, 7):
    for id_member in range(1, 17):
        if len(str(id_member)) != 2:
            video_id = f'0{id_member}'
        else:
            video_id = f'{id_member}'

        filename = f'member_standing_movie_0{gen}{video_id}.usme'
        link = f'{MAIN_PATH}{OPTIONAL_PATH['member-standing']}/{filename}'
        if os.path.exists(f'{download_path}/{filename[:-5]}.mp4'):
            print(f'{filename[:-5]} already exist')
            continue
        response = requests.get(link, stream=True)
        if response.status_code != 200:
            continue
        path_raw = os.path.join(base_dir, temp, filename)
        if not os.path.exists(path_raw):
            download(response,filename)
        print('demuxing...')
        usm_extractor(path_raw,KEY,f'{base_dir}/temp')
        member_standing(filename[:-5], download_path)
        id_member+=1
        os.remove(path_raw)
        print(f'{filename[:-5]} downloaded')