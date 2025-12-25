import os
from pathlib import Path

import torch
import torchaudio
from pydantic import TypeAdapter

from models import BookInfo
from tts import TextToSpeechService

data = "data"
data_file = Path(f"{data}/output.json")


def generate_chapter_audio(text: str, output: Path, audio_prompt_path: str):
    dynamic_cfg = 0.3
    exaggeration = 0.3

    sample_rate, audio_array = tts.long_form_synthesize(
        text,
        exaggeration=exaggeration,
        cfg_weight=dynamic_cfg,
        audio_prompt_path=audio_prompt_path,
    )

    print(f"Saving file {output}")

    torchaudio.save(
        uri=output,
        src=torch.from_numpy(audio_array).unsqueeze(0),
        sample_rate=sample_rate,
    )


if __name__ == "__main__":
    tts = TextToSpeechService()

    adapter = TypeAdapter(list[BookInfo])

    infos = None

    with open(data_file, "rb") as file:
        infos = adapter.validate_json(file.read())

    for info in infos:
        os.makedirs(f"{data}/{info.idx}", exist_ok=True)

        for chapter in info.chapters:
            out_voice = Path(f"{data}/{info.idx}/C{chapter.idx:02}.wav")

            if out_voice.exists():
                print(f"Skipping {out_voice}")
                continue

            text = chapter.name + "\n" + "\n".join(chapter.paragraphs)

            print(f"#####\n##### Generating {out_voice}\n#####")

            tts.aggressive_cleanup()

            generate_chapter_audio(text, out_voice, "samples/rpike01.wav")
