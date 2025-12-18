import torch
import torchaudio

from tts import TextToSpeechService

if __name__ == "__main__":
    tts = TextToSpeechService()

    text = """Elan Morin appears at the mountain where he promises that it won't end that easily for the Dragon."""

    exaggeration = 0.3
    dynamic_cfg = 0.3

    sample_rate, audio_array = tts.long_form_synthesize(
        text,
        exaggeration=exaggeration,
        cfg_weight=dynamic_cfg,
        audio_prompt_path="samples/rpike01.wav",
    )

    torchaudio.save(
        uri="out.wav",
        src=torch.from_numpy(audio_array).unsqueeze(0),
        sample_rate=sample_rate,
    )
