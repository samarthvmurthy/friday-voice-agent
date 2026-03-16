# 🎙️ Friday — Voice-Controlled Browser Agent

> Say *"hey Friday"* and watch AI browse the web for you.

Friday is a hands-free, wake-word-activated voice assistant that controls a real browser using **Google Gemini's multimodal vision and planning capabilities**. Just speak a task — Friday navigates, clicks, fills forms, and reports back when done.

Built for the **Google Gemini Hackathon**.

---

## ✨ Features

- 🎙️ **Wake-word activation** — always listening for *"hey Friday"*, completely hands-free
- 🧠 **Gemini Vision + Planning** — Gemini sees the live browser screen and plans multi-step tasks
- 🖥️ **Floating HUD** — persistent GUI showing live agent status and action log
- 🔊 **Voice feedback** — Friday speaks its status back to you in real time
- ⏹️ **Cancellable tasks** — stop mid-execution with a single button press
- 🔇 **Mute toggle** — silence voice output without interrupting the agent
- ⌨️ **Browser shortcuts** — back, refresh, new tab, home — all from the GUI
- 🔁 **Loop detection** — automatically recovers from stuck states

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Main Thread (GUI)                  │
│                   Tkinter HUD                        │
│         status · log · mic · stop · mute             │
└───────────────────┬─────────────────────────────────┘
                    │ callbacks + threading.Event
┌───────────────────▼─────────────────────────────────┐
│             Background Thread (Agent Loop)           │
│                                                      │
│  VoiceListener ──► wake word ──► record command      │
│                                       │              │
│                              asyncio event loop      │
│                                       │              │
│                              browser-use Agent       │
│                                       │              │
│                            Google Gemini API         │
│                         (Vision + Planning)          │
│                                       │              │
│                             Playwright Browser       │
└─────────────────────────────────────────────────────┘
```

Two threads run in parallel:
- **Main thread** — Tkinter GUI, never blocks
- **Agent thread** — owns its own `asyncio` event loop, handles voice I/O and all browser automation

Tasks are wrapped as `asyncio.Task` objects so they can be cancelled cleanly at any point via `loop.call_soon_threadsafe(task.cancel)`.

---

## 🛠️ Tech Stack

### Google Technologies
| Technology | Role |
|---|---|
| **Gemini API** | Core LLM — reasoning, planning, and decision-making |
| **Gemini Vision** | Reads and understands the live browser screen |
| **Gemini Planning** | Decomposes complex tasks into multi-step execution plans |
| **google-genai SDK** | Official Google SDK for Gemini API access |
| **langchain-google-genai** | LangChain integration for Gemini |

### Supporting Stack
| Technology | Role |
|---|---|
| `browser-use` | Browser agent framework |
| `Playwright` | Browser engine (via browser-use) |
| `Vosk` | Offline wake-word detection + speech recognition |
| `SpeechRecognition` | Microphone input |
| `pyttsx3` | Text-to-speech (Friday's voice) |
| `Tkinter` | Floating HUD / GUI |
| `pyautogui` | Browser keyboard shortcut passthrough |
| `python-dotenv` | API key management |
| `Python 3.11+` | Language |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- A [Gemini API key](https://aistudio.google.com/app/apikey) from Google AI Studio
- A working microphone

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/friday.git
cd friday

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium

# 5. Set up your API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your key from [Google AI Studio](https://aistudio.google.com/app/apikey) — it's free.

### Run

```bash
python main.py
```

Friday will calibrate your microphone on startup, then say *"Friday is ready."*

---

## 🎤 Usage

### Voice Control
1. Say **"hey Friday"** to activate
2. Wait for the *"Listening"* confirmation
3. Speak your task clearly:
   - *"Search for flights from New York to London next month"*
   - *"Go to YouTube and find a tutorial on Python asyncio"*
   - *"Open Gmail and summarize my latest unread emails"*
4. Friday will confirm your command and start executing
5. Say or press **Stop** to cancel at any time

### GUI Controls

| Button | Action |
|---|---|
| 🎙️ Mic | Manually trigger listening (no wake word needed) |
| ⏹️ Stop | Cancel the current task immediately |
| 🔇 Mute | Toggle voice feedback on/off |
| ← Back | Browser back (only when no task running) |
| ↻ Refresh | Browser refresh (only when no task running) |
| + New Tab | Open a new browser tab |
| 🏠 Home | Navigate to browser home |
| ✕ Quit | Exit Friday |

---

## 📁 Project Structure

```
friday/
├── main.py          # Entry point — orchestrates all components
├── agent.py         # Gemini LLM setup via langchain-google-genai
├── browser.py       # Browser profile configuration for browser-use
├── voice.py         # Wake-word detection, recording, TTS
├── gui.py           # Tkinter floating HUD
├── .env             # Your API keys (never commit this)
├── .env.example     # Template for environment variables
└── requirements.txt # Python dependencies
```

---

## ⚙️ Configuration

Key parameters in `main.py` you can tune:

```python
agent = Agent(
    use_vision=True,          # Gemini reads the screen visually
    enable_planning=True,     # Multi-step task decomposition
    max_failures=5,           # Retries before giving up
    loop_detection_enabled=True,  # Detects and escapes stuck loops
)
```

---

## 🔧 Troubleshooting

**Friday doesn't hear the wake word**
- Run with a quiet background — Vosk calibrates to ambient noise on startup
- Speak clearly and at a normal pace
- Check your microphone is set as the default input device

**Browser doesn't open**
- Make sure you ran `playwright install chromium`
- Check your `browser.py` profile configuration

**Gemini API errors**
- Verify your `GEMINI_API_KEY` in `.env` is valid and has quota
- Check [Google AI Studio](https://aistudio.google.com) for usage limits

**Task gets stuck**
- Press the **Stop** button in the GUI — this cleanly cancels the async task
- `loop_detection_enabled=True` will also auto-recover in most cases

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [browser-use](https://github.com/browser-use/browser-use) — the incredible browser agent framework that makes this possible
- [Google Gemini](https://deepmind.google/technologies/gemini/) — for vision and planning capabilities
- [Vosk](https://alphacephei.com/vosk/) — for fast, offline speech recognition

---

*Built with ❤️💜 for the Google Gemini Hackathon*
