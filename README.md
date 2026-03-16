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
| **Gemini API** (`gemini-2.5-flash`) | Core LLM — reasoning, planning, and decision-making |
| **Gemini Vision** | Reads and understands the live browser screen |
| **Gemini Planning** | Decomposes complex tasks into multi-step execution plans |
| **`ChatGoogle`** (`browser_use.llm.google`) | Native Google Gemini API integration used in `agent.py` |
| **Google AI Studio** | API key management and usage monitoring |

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
├── agent.py         # Google Gemini LLM setup via ChatGoogle (gemini-2.5-flash)
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

## 🧪 Reproducible Testing Instructions

> **No microphone? No problem.** Friday has a manual trigger button in the GUI so you can test every feature without ever saying a word.

### Setup (5 minutes)

```bash
# 1. Clone and enter the repo
git clone https://github.com/yourusername/friday.git
cd friday

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Install the browser engine
playwright install chromium

# 5. Add your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com/app/apikey) — takes 30 seconds.

---

### Run Friday

```bash
python main.py
```

Wait for the floating HUD to appear and Friday to say **"Friday is ready."**

---

### How to give commands (two ways)

**Option A — Voice (recommended)**
Say *"hey Friday"* clearly, wait for *"Listening"*, then speak your task.

**Option B — Manual button (no microphone needed)**
Click the 🎙️ mic button in the HUD, then speak your task. Identical behavior, no wake word required.

---

### Suggested Test Commands

Try these in order — they go from simple to complex and cover the full range of Friday's capabilities:

**1. Sanity check**
> *"Go to google.com"*

The browser should open and navigate to Google. Friday confirms when done.

**2. Google Search + Gemini vision**
> *"Search Google for the latest Gemini AI news and tell me the top result"*

Friday searches, reads the results page visually using Gemini, and speaks the top headline back to you.

**3. Google News summarization**
> *"Open Google News and summarize the top 3 stories right now"*

Friday navigates to `news.google.com`, reads the live headlines using Gemini vision, and gives you a spoken summary.

**4. YouTube navigation**
> *"Go to YouTube and find the most viewed video about Google Gemini"*

Multi-step task — Friday searches, reads view counts visually, and opens the top result.

**5. The fun one — Rickroll**
> *"Hey Friday, rickroll me"*

Friday interprets intent (not just literal words), navigates to YouTube, finds Rick Astley's *Never Gonna Give You Up*, and plays it. Tests Gemini's reasoning ability.

**6. Multi-step Google task**
> *"Open Google Maps and find the highest rated coffee shop near me"*

Tests location-aware browsing, reading ratings and reviews, and multi-step decision-making — all in one command.

---

### Test Task Cancellation

1. Give Friday a long task: *"Search Google for every country in the world and list them all"*
2. While it's running, press **⏹️ Stop** in the HUD
3. Friday should say *"Stopped."* and return to idle within 2 seconds — no crash, no hang

---

### What to look for

| Signal | What it means |
|---|---|
| HUD status changes in real time | Agent loop and GUI are communicating correctly |
| Browser navigates without manual input | browser-use + Playwright working |
| Friday speaks results back | Gemini vision successfully read the page |
| Stop button cancels cleanly | Async task cancellation working |
| Log panel fills with action steps | Gemini planning is decomposing tasks correctly |

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

## ☁️ Google API Integration — Proof of Use

Friday's entire AI brain is powered by a **direct call to Google's Gemini API** via the official `ChatGoogle` client from `browser-use`:

```python
# agent.py
from browser_use.llm.google.chat import ChatGoogle


def create_llm(api_key: str) -> ChatGoogle:
    """
    Creates a Google Gemini LLM instance via the official Google API.
    Model: gemini-2.5-flash — Google's latest multimodal model.
    API key sourced from GEMINI_API_KEY environment variable.
    Used by browser-use Agent for vision, planning, and task execution.
    """
    return ChatGoogle(
        model="gemini-2.5-flash",
        api_key=api_key,
        temperature=0.1,
    )
```

Every voice command Friday receives triggers a live call to `gemini-2.5-flash` — Google's latest model — for vision-based screen reading, multi-step task planning, and action execution. No other LLM provider is used anywhere in the codebase.

API usage is tracked and visible in **Google AI Studio** — 500+ requests, 5M+ input tokens, 100% success rate logged over 28 days of development.

> 🔗 **[View `agent.py` on GitHub](https://github.com/yourusername/friday/blob/main/agent.py)**

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

*Built with ❤️ for the Google Gemini Hackathon*
