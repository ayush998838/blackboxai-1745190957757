# Dexent.ai MVP - Quick Start Guide

This MVP version of Dexent.ai provides a basic Windows desktop client and backend server with placeholder accent conversion functionality for testing purposes.

## Prerequisites

- Python 3.10+
- PyQt5
- Required Python packages (see requirements.txt)

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv venv
venv\\Scripts\\activate  # Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables (optional):

- `DATABASE_URL` (if using database)
- `FIREBASE_API_KEY`, `FIREBASE_PROJECT_ID`, `FIREBASE_APP_ID` (if using Firebase)

4. Run the Windows desktop client:

```bash
python windows_client.py
```

The client will start in the system tray and manage the backend server automatically.

## Testing

- Use the system tray icon to start/stop audio processing.
- Open the web dashboard for settings and monitoring.
- Note: Accent conversion currently uses placeholder silent audio output.

## Next Steps

- Replace placeholder accent conversion with real models.
- Implement real-time audio stream processing.
- Add call detection and automatic processing start.

This MVP is for initial testing and feedback. A more advanced version will be provided later.

---
