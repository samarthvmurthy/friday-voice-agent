import pyautogui
import pyperclip
import time

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15

_FAILSAFE_MARGIN = 5  # pixels — avoid top-left corner that triggers FAILSAFE


def _type_text(text: str):
    """Use clipboard paste for reliable unicode input."""
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")


def _safe_coords(x: int, y: int) -> tuple[int, int] | None:
    """Return (x, y) or None if in pyautogui FAILSAFE zone."""
    if x < _FAILSAFE_MARGIN and y < _FAILSAFE_MARGIN:
        print(f"      Skipping failsafe-zone coordinates ({x}, {y}).")
        return None
    return x, y


def execute_actions(actions_data: dict, post_action_delay: float = 0.05):
    understanding = actions_data.get("understanding", "")
    plan = actions_data.get("plan", "")
    actions = actions_data.get("actions", [])

    if understanding:
        print(f"\n  See:  {understanding}")
    if plan:
        print(f"  Plan: {plan}")

    if not actions:
        print("  No actions to execute.")
        return

    print(f"  Executing {len(actions)} action(s):")

    for i, action in enumerate(actions):
        atype = action.get("type", "")
        desc = action.get("description", "")
        print(f"    [{i+1}] {atype}: {desc}", flush=True)

        try:
            if atype == "click":
                coords = _safe_coords(int(action["x"]), int(action["y"]))
                if coords:
                    pyautogui.click(*coords)

            elif atype == "double_click":
                coords = _safe_coords(int(action["x"]), int(action["y"]))
                if coords:
                    pyautogui.doubleClick(*coords)

            elif atype == "right_click":
                coords = _safe_coords(int(action["x"]), int(action["y"]))
                if coords:
                    pyautogui.rightClick(*coords)

            elif atype == "drag":
                x1, y1 = int(action["x"]), int(action["y"])
                x2, y2 = int(action["x2"]), int(action["y2"])
                pyautogui.moveTo(x1, y1, duration=0.3)
                pyautogui.dragTo(x2, y2, duration=0.5, button="left")

            elif atype == "key":
                pyautogui.press(action["key"].lower())

            elif atype == "hotkey":
                keys = action.get("keys", [])
                if keys:
                    pyautogui.hotkey(*keys)

            elif atype == "type":
                _type_text(action["text"])

            elif atype == "wait":
                time.sleep(float(action.get("seconds", 1)))

            elif atype == "scroll":
                x = int(action.get("x", pyautogui.size().width // 2))
                y = int(action.get("y", pyautogui.size().height // 2))
                direction = action.get("direction", "down")
                raw_amount = int(action.get("amount", 300))
                clicks = max(1, raw_amount // 100)
                delta = -clicks if direction == "down" else clicks
                pyautogui.moveTo(x, y)
                pyautogui.scroll(delta)

            else:
                print(f"      Skipping unsupported action: {atype}")

        except Exception as e:
            print(f"      Error: {e}")

        time.sleep(post_action_delay)

    print("  Done.\n")
