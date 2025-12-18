# TTS for WoT

- TTS: [chatterbox](https://github.com/resemble-ai/chatterbox)
- Web Scrapping: TBD

## Setup

- Install `uv`
    - [Installation docs](https://docs.astral.sh/uv/getting-started/installation/)
- Setup dependencies
    - `uv sync`
- Activate env
    - `source .venv/bin/activate`
- Install NLTK data for tokenization
    - `python -c "import nltk; nltk.download('punkt_tab')"`

## Record samples from internal MacOS audio

- Install dependencies
    - `brew install ffmpeg blackhole-2ch`
- Restart computer
- [Setup multi-output device](https://github.com/ExistentialAudio/BlackHole/wiki/Multi-Output-Device)

To record:

```sh
ffmpeg -f avfoundation -i ":BlackHole 2ch" output.wav
```

Then press `q` to stop and quit.

## Folder setup

- `hout` is where all the HTMLs are stored
- `data` is where the treated text is stored
- `samples` is where voice samples are stored
