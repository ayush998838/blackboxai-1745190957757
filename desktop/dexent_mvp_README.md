# Dexent.ai MVP with ECAPA-TDNN and YourTTS

This MVP demonstrates a minimal pipeline for accent conversion using:

- ECAPA-TDNN for speaker embedding extraction
- YourTTS or StyleVC for accent-shifted voice synthesis (placeholder in this MVP)
- Whisper or other ASR for transcription (placeholder in this MVP)

## Requirements

- Python 3.10+
- torch
- soundfile
- numpy

Install dependencies:

```
pip install torch soundfile numpy
```

## Usage

Run the accent conversion pipeline on an input audio file:

```
python dexent_mvp_ecapa_yourtts.py input.wav american output.wav
```

This will:

1. Transcribe the input audio (dummy transcription)
2. Extract speaker embedding (dummy embedding)
3. Synthesize speech with the target accent (dummy silent audio)
4. Save the output audio to `output.wav`

## Next Steps

- Replace placeholder functions with real ECAPA-TDNN and YourTTS implementations
- Integrate real ASR for transcription
- Extend to real-time audio stream processing
- Integrate with desktop client for background processing

This MVP is for initial testing and demonstration purposes.
