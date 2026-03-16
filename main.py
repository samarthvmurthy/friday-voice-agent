import os
import sys
import time
import asyncio
import threading
import pyautogui
from dotenv import load_dotenv

from browser_use import Agent

from gui import FloatingGUI
from voice import VoiceListener, speak, set_muted
from browser import get_browser_profile
from agent import create_llm

load_dotenv()

pyautogui.FAILSAFE = False  # prevent accidental abort during browser nav shortcuts

_active_task: list[asyncio.Task | None]              = [None]
_agent_loop:  list[asyncio.AbstractEventLoop | None] = [None]


async def run_task(task: str, llm, browser_profile, gui: FloatingGUI):
    def on_step(state, model_output, result):
        try:
            if model_output and hasattr(model_output, 'action') and model_output.action:
                desc = str(model_output.action[0])[:80]
                gui.add_log(desc, 'active')
                gui.set_state('executing', desc)
        except Exception:
            pass

    def on_done(history):
        try:
            final = history.final_result() if hasattr(history, 'final_result') else ''
            if final:
                gui.add_log(str(final)[:80], 'ok')
        except Exception:
            pass

    agent = Agent(
        task=task,
        llm=llm,
        browser_profile=browser_profile,
        register_new_step_callback=on_step,
        register_done_callback=on_done,
        use_vision=True,
        enable_planning=True,
        max_failures=5,
        loop_detection_enabled=True,
        generate_gif=False,
    )

    await agent.run()


def _browser_shortcut(keys):
    """Send a keyboard shortcut to whatever window is in focus (the browser)."""
    try:
        pyautogui.hotkey(*keys)
    except Exception as e:
        print(f'  Shortcut error: {e}', flush=True)


def agent_loop(gui: FloatingGUI, llm, browser_profile,
               manual_trigger: threading.Event):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _agent_loop[0] = loop

    voice = VoiceListener()
    voice.calibrate()

    speak("Friday is ready. Say hey Friday or press speak to give a command.")

    while True:
        try:
            # ── Wait for wake word OR mic button ────────────────
            gui.set_state('idle')
            manual_trigger.clear()
            voice.wait_for_wake(manual_event=manual_trigger)

            # ── Record command ───────────────────────────────────
            gui.set_state('wake')
            speak("Listening.")
            command = voice.record_command()

            if not command:
                gui.set_state('idle')
                continue

            print(f'\nCommand: "{command}"', flush=True)
            gui.add_log(command, 'command')
            gui.set_state('processing', command)
            speak(f"Got it. {command}.")

            # ── Run Browser Use as a cancellable async task ──────
            async def _run():
                await run_task(command, llm, browser_profile, gui)

            task = loop.create_task(_run())
            _active_task[0] = task

            try:
                loop.run_until_complete(task)
                gui.add_log('Task complete.', 'ok')
                gui.set_state('done', command)
                speak("Done!")
            except asyncio.CancelledError:
                gui.add_log('Stopped by user.', 'warn')
                gui.set_state('idle')
                speak("Stopped.")
            finally:
                _active_task[0] = None

            time.sleep(2)

        except Exception as e:
            print(f'Error: {e}', flush=True)
            gui.add_log(str(e)[:60], 'error')
            gui.set_state('error', str(e)[:40])
            speak("Sorry, something went wrong.")
            time.sleep(3)


def main():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print('Error: GEMINI_API_KEY not set in .env')
        sys.exit(1)

    print('Initializing...', flush=True)

    llm             = create_llm(api_key)
    browser_profile = get_browser_profile()
    manual_trigger  = threading.Event()

    def on_quit():
        speak("Goodbye.")
        time.sleep(0.8)
        os._exit(0)

    def on_mic_click():
        print('  [mic] Manual trigger.', flush=True)
        manual_trigger.set()

    def on_stop():
        task = _active_task[0]
        loop = _agent_loop[0]
        if task and loop and not task.done():
            print('  [stop] Cancelling task.', flush=True)
            loop.call_soon_threadsafe(task.cancel)
        else:
            print('  [stop] No active task.', flush=True)

    # Browser nav shortcuts — only safe to send when no task is running
    def on_back():
        if not _active_task[0]:
            _browser_shortcut(['alt', 'left'])

    def on_refresh():
        if not _active_task[0]:
            _browser_shortcut(['f5'])

    def on_new_tab():
        if not _active_task[0]:
            _browser_shortcut(['ctrl', 't'])

    def on_home():
        if not _active_task[0]:
            _browser_shortcut(['alt', 'home'])

    def on_mute_toggle(muted: bool):
        set_muted(muted)
        print(f'  [mute] {"muted" if muted else "unmuted"}', flush=True)

    gui = FloatingGUI(
        on_quit=on_quit,
        on_mic_click=on_mic_click,
        on_stop=on_stop,
        on_back=on_back,
        on_refresh=on_refresh,
        on_new_tab=on_new_tab,
        on_home=on_home,
        on_mute_toggle=on_mute_toggle,
    )

    t = threading.Thread(
        target=agent_loop,
        args=(gui, llm, browser_profile, manual_trigger),
        daemon=True,
    )
    t.start()

    gui.start()


if __name__ == '__main__':
    main()
