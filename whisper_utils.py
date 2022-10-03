import whisper

model = None


def start_whisper():
    global model
    model = whisper.load_model("base")


def transcribe(file_name, mode):
    global model

    result = model.transcribe(file_name, task=mode)
    # result = model.transcribe(file_name, language="english")

    # load audio and pad/trim it to fit 30 seconds
    # audio = whisper.load_audio(file_name)
    # audio = whisper.pad_or_trim(audio)

    # # make log-Mel spectrogram and move to the same device as the model
    # mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # # detect the spoken language
    # _, probs = model.detect_language(mel)
    # print(f"Detected language: {max(probs, key=probs.get)}")

    # # decode the audio
    # options = whisper.DecodingOptions()
    # result = whisper.decode(model, mel, options)

    # text = result.text

    text = result["text"]
    return text
