from PyCriCodecs import USM, ACB, AWB, CPK
import os
import builtins
import inspect

# video = "live_finish_movie_0124200.usme"
# key = 0x0013F11BC5510101
out = "temp"
os.makedirs(out, exist_ok=True)

_real_open = builtins.open

def safe_open(file, mode='r', *args, **kwargs):
    
    try:
        if isinstance(file, str) and "\\" in file:
            for frame in inspect.stack()[1:8]:
                fname = frame.filename.replace("\\", "/")
                if "/PyCriCodecs/usm.py" in fname or fname.endswith("/usm.py") or "PyCriCodecs/usm.py" in fname:
                    cleaned_basename = os.path.basename(file.replace("\\", "/"))
                    sanitized_path = os.path.join(out, cleaned_basename)
                    return _real_open(sanitized_path, mode, *args, **kwargs)
    except Exception:
        pass

    return _real_open(file, mode, *args, **kwargs)

def usm_extractor(video, key, output):
    builtins.open = safe_open

    try:
        usm = USM(video, key=key)
        usm.extract(output)
    finally:
        builtins.open = _real_open
        
def cpk_extractor(video, key, output):
    builtins.open = safe_open

    try:
        cpk = CPK(video, key=key)
        cpk.extract(output)
    finally:
        builtins.open = _real_open

def audio_extractor(audio, key, out):
    builtins.open = safe_open
    
    try:
        if audio[-3:] == "acb":
            audioObj = ACB(audio)
            audioObj.extract(dirname=out, decode=True, key=key)
        elif audio[-3:] == "awb":
            audioObj = AWB(audio)
            audioObj.extract(out)
        
    finally:
        builtins.open = _real_open

