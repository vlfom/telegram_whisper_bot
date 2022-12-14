import whisper

MODEL_SIZE = "large"

whisper_state = dict(
    model=None
)


def start_whisper():
    whisper_state["model"] = whisper.load_model(MODEL_SIZE)


async def transcribe(file_name, mode):
    model = whisper_state["model"]
    result = model.transcribe(file_name, task=mode)

    text = result["text"]
    return text
