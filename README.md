# Nogifes Downloader
Tools for downloading Nogizaka46 Rhythm Festival content.

## Requirements

### Python
Install Python 3.10 or above from [https://www.python.org/downloads/](https://www.python.org/downloads/)

### Microsoft C++ Build Tools
Install Microsoft C++ Build Tools 14.0 or above from [https://visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

> **Installation tip:** When the installer opens, check **"Desktop development with C++"** workload, then click Install.

## Installation

1. Clone this repository
```bash
   git clone https://github.com/<your-username>/nogifes-downloader.git
   cd nogifes-downloader
```

2. Install Python dependencies
```bash
   pip install -r requirements.txt
```

3. Install PyCriCodecs
```bash
   git clone https://github.com/Youjose/PyCriCodecs.git
   cd PyCriCodecs
   pip install .
   cd ..
```

4. Run the application
```bash
   python nogifes_downloader.py
```
