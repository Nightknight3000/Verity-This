"""
Verity This! -- Native GUI
==========================

A point-and-click graphical front-end for the "Verity This!" tool that
talks directly to the ORIGINAL, UNMODIFIED business logic in verity_this.py
and src/ -- no subprocess, no re-implemented algorithms.

How it works
------------
Every question the CLI would normally ask via input() goes through exactly
one low-level function: src.io.read_inputs._get_input (plus one raw
input() call at the very end of verity_this.main() for the "Restart?"
question). This file monkey-patches only those entry points at runtime:

  * src.io.read_inputs._get_input   -> shows buttons, blocks until clicked
  * verity_this.input                -> shows Yes/No buttons ("Restart?")
  * print_colour (in all 3 modules that import it) -> writes to the GUI log

Everything else -- get_mode, get_init, get_and_check_calls, the num_doubles
consistency checks, calc_n_assembly, calc_c_dissection, the triumph sort,
the whole round loop in verity_this.main() -- runs completely untouched,
in a background thread. This means any future change to the algorithms in
src/ is picked up automatically without ever touching this file again.

Usage
-----
    python gui_native.py

Place this file in the repository root (next to verity_this.py).

Requirements
------------
Only the Python standard library (tkinter).
"""

from __future__ import annotations

import os
import queue
import re
import sys
import threading
import traceback
import tkinter as tk
from tkinter import scrolledtext


# ---------------------------------------------------------------------------
# Make sure "import verity_this" / "import src...." resolves regardless of
# the current working directory.
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


# ---------------------------------------------------------------------------
# Visual style
# ---------------------------------------------------------------------------

BG = "#1e1e1e"
FG_DEFAULT = "#e0e0e0"
PANEL_BG = "#242424"
BTN_BG = "#333333"
BTN_ACTIVE_BG = "#4fa8ff"
FONT = ("Consolas", 11)
FONT_BOLD = ("Consolas", 11, "bold")

# Mirrors src/utils/constants.py COLOURS -- print_colour receives these
# names directly (no ANSI parsing needed, unlike a subprocess wrapper).
COLOUR_NAME_TO_HEX = {
    "default": None,
    "lightred": "#ff8a80",
    "green": "#69f0ae",
    "yellow": "#ffd54f",
    "blue": "#64b5f6",
    "purple": "#ce93d8",
    "cyan": "#4dd0e1",
    "grey": "#9e9e9e",
    "red": "#ff5252",
    "heavygreen": "#00e676",
}

# Every Text-widget tag actually configured in _build_ui: the colour tags
# with a real hex value, plus the two special tags ("default" has no hex
# and is therefore never configured as a tag -- it just means "no tag").
VALID_LOG_TAGS = {name for name, hexcolor in COLOUR_NAME_TO_HEX.items() if hexcolor} | {"echo", "system", "call_echo"}

ANSI_RE = re.compile(r"\x1b\[\d+m")

# verity_this.py's own banner explains typing 'h'/'help', 'restart', and
# 'exit' -- all now covered by the GUI's buttons instead of free text, so
# these three lines (unlike the rest of the banner) are suppressed from the
# GUI log. Matched by exact stripped text rather than touching verity_this.py
# itself, so the console version keeps showing them unchanged.
SUPPRESSED_INTRO_LINES = {
    "use 'h' or 'help' anytime for instructions,",
    "'restart' to restart the application,",
    "or 'exit' to end the application",
}

# src/io/read_inputs.py's _get_calls prints exactly this (in green) when it
# auto-computes the third ('right') call from the first two:
#   "...Outside statue right: tt\n" / "...Inside wall right: tt\n"
AUTOFILL_RE = re.compile(r"(Outside statue|Inside wall) right: ([a-z]{2})")


def clean_prompt(text: str) -> str:
    """Strips ANSI codes / tabs / trailing colon so a raw CLI prompt string
    reads well as a GUI label."""
    text = ANSI_RE.sub("", text).replace("\t", "").strip()
    if text.endswith(":"):
        text = text[:-1]
    return text.strip()


# ---------------------------------------------------------------------------
# Friendly button labels for each constants.py dict, keyed by input_type.
# (Hardcoded from the actual src/utils/constants.py content -- not guessed.)
# ---------------------------------------------------------------------------

MODE_LABELS = {
    "normal": "Normal",
    "all_normal": "All Normal",
    "triumph": "Triumph",
    "challenge": "Challenge",
    "hard_challenge": "Hard Challenge",
    "triumph+challenge": "Triumph + Challenge",
    "triumph+hard_challenge": "Triumph + Hard Challenge",
}
N_STRAT_LABELS = {"double-up": "Double-Up", "speed": "Speed"}
POSITION_LABELS = {
    "outside": "Outside",
    "left": "Inside Left",
    "middle": "Inside Middle",
    "right": "Inside Right",
}
NUM_DOUBLES_LABELS = {"0": "0 (no doubles)", "1": "1 double", "3": "3 (all doubled)"}
BODY_LABELS = {
    "cc": "Sphere (cc)",
    "ss": "Cube (ss)",
    "tt": "Pyramid (tt)",
    "st": "Prism (st)",
    "cs": "Cylinder (cs)",
    "ct": "Cone (ct)",
}

# Inside walls show the 2D symbol pairs directly (unlike the outside
# statues, which show the corresponding 3D body) -- so 'l'/'m'/'r' options
# are labelled as a combination of their two 2D parts when io_context is
# "inside", instead of the 3D body name used for "outside".
SHAPE_2D_NAMES = {"c": "Circle", "s": "Square", "t": "Triangle"}


def body_2d_label(body_key: str) -> str:
    return " + ".join(SHAPE_2D_NAMES.get(ch, ch) for ch in body_key)


INIT_OPTIONS = ["cst", "cts", "sct", "stc", "tcs", "tsc"]

LABEL_MAPS = {
    "mode": MODE_LABELS,
    "n_strat": N_STRAT_LABELS,
    "self_pos": POSITION_LABELS,
    "number_of_doubles": NUM_DOUBLES_LABELS,
    "l": BODY_LABELS,
    "m": BODY_LABELS,
    "r": BODY_LABELS,
}

# Short prefixes used in the log to show which question an echoed answer
# belongs to, e.g. "> Mode: Normal" or "> Inside Left: Sphere (cc)".
SHORT_PROMPT_LABELS = {
    "mode": "Mode",
    "n_strat": "Strategy",
    "init": "Init",
    "self_pos": "Position",
    "number_of_doubles": "Doubles",
    "yesno": "Restart?",
}
FIELD_SHORT_NAME = {"l": "Left", "m": "Middle", "r": "Right"}


def short_prompt_label(input_type: str, io_context: "str | None") -> str:
    if input_type in FIELD_SHORT_NAME:
        side = "Inside" if io_context == "inside" else "Outside"
        return f"{side} {FIELD_SHORT_NAME[input_type]}"
    return SHORT_PROMPT_LABELS.get(input_type, str(input_type).replace("_", " ").title())

# src/io/read_inputs.py now checks, per field, that the 'left' call contains
# init[0], 'middle' contains init[1], and 'right' (when asked directly)
# contains init[2] -- before the field is even accepted. These map each
# input_type to that required index so the GUI can pre-emptively grey out
# any body button that would fail the check, instead of letting the user
# click it and only then showing the error.
REQUIRED_INIT_INDEX = {"l": 0, "m": 1, "r": 2}


def required_init_letter(input_type: str, current_init: "str | None") -> "str | None":
    """Which init letter (if any) a body-call answer for this input_type
    must contain, given the init chosen earlier this round."""
    idx = REQUIRED_INIT_INDEX.get(input_type)
    if idx is None or not current_init or len(current_init) <= idx:
        return None
    return current_init[idx]


def is_body_option_allowed(body_key: str, required_letter: "str | None") -> bool:
    """Mirrors src.io.read_inputs._get_calls's own `init[i] in call` check."""
    if required_letter is None:
        return True
    return required_letter in body_key


def remaining_symbol_budget(consumed: str = "") -> dict:
    """Each of 'c', 's', 't' may occur at most twice in total across
    left+middle+right (src.io.read_inputs.get_and_check_calls's
    `total_symbols_match` check). Given the symbols already used by
    earlier fields in this same call-group, returns how many of each
    symbol are still available."""
    budget = {"c": 2, "s": 2, "t": 2}
    for ch in consumed:
        if ch in budget:
            budget[ch] -= 1
    return budget


def is_body_option_within_budget(body_key: str, budget: dict) -> bool:
    for ch in set(body_key):
        if body_key.count(ch) > budget.get(ch, 0):
            return False
    return True


def predict_auto_right(left: str, middle: str, shape_key_order: "list[str] | None") -> str:
    """Mirrors src.io.read_inputs._get_calls's exact formula for the
    auto-computed 'right' call, so the GUI can predict it before it
    actually happens and check whether it would contain the required
    init[2] letter."""
    order = shape_key_order or ["c", "s", "t"]
    combo = left + middle
    return ''.join([s for s in order * 2 if combo.count(s) < 2][:2])


def is_num_doubles_option_allowed(value: str, call_value: "str | None") -> bool:
    """Mirrors verity_this.py's own _get_calls consistency check between the
    already-chosen single call (for the player's own position) and the
    number-of-doubles answer: num_doubles=0 is impossible if that call is
    doubled, and num_doubles=3 is impossible if it isn't."""
    if not call_value or len(call_value) != 2:
        return True
    doubled = call_value[0] == call_value[1]
    if doubled and value == "0":
        return False
    if not doubled and value == "3":
        return False
    return True


def compute_disabled_values(input_type, options, required_letter, current_init,
                            io_context, last_call_answer, shape_key_order,
                            previous_question=None):
    """Pure decision logic for which option *values* should be disabled for
    a given question. Deliberately does nothing (returns an empty set) for
    any input_type other than the body-call fields 'l', 'm', 'r' and
    'number_of_doubles' -- mode, n_strat, self_pos and init are never
    touched here.

    previous_question, if given, is the (input_type, io_context) of the
    question shown immediately before this one -- used to make sure a
    'left' answer is only treated as feeding into 'middle' when it was
    truly asked right before it in the same call-group, not left over from
    an earlier round's single-position call (e.g. 'left' in round 1
    followed by an unrelated 'middle' in round 2)."""
    if input_type == "number_of_doubles":
        call_value = None
        if last_call_answer is not None and last_call_answer[0] in ("l", "m", "r"):
            call_value = last_call_answer[2]
        return {
            value for _, value in options
            if value is not None and not is_num_doubles_option_allowed(value, call_value)
        }

    if input_type not in ("l", "m", "r"):
        return set()

    consumed = ""
    if (
        input_type == "m"
        and previous_question == ("l", io_context)
        and last_call_answer is not None
        and last_call_answer[:2] == ("l", io_context)
    ):
        consumed = last_call_answer[2] or ""
    budget = remaining_symbol_budget(consumed)

    right_letter = None
    if consumed and current_init and len(current_init) > 2:
        right_letter = current_init[2]

    def rejected(value: str) -> bool:
        if not is_body_option_allowed(value, required_letter):
            return True
        if not is_body_option_within_budget(value, budget):
            return True
        if input_type == "m" and consumed and right_letter is not None:
            predicted_right = predict_auto_right(consumed, value, shape_key_order)
            if len(predicted_right) != 2 or right_letter not in predicted_right:
                return True
        return False

    return {value for _, value in options if value is not None and rejected(value)}


# ---------------------------------------------------------------------------
# Thread bridge: the worker thread (running the real verity_this.main())
# only ever talks to this object; it never touches Tkinter directly.
# ---------------------------------------------------------------------------

class InputBroker:
    EXIT = object()
    RESTART = object()

    def __init__(self, shared_q: "queue.Queue"):
        self.shared_q = shared_q
        self.answer_q: "queue.Queue" = queue.Queue()

    def ask(self, input_type, prompt, ref, is_optional=False):
        self.shared_q.put(("question", input_type, prompt, dict(ref), is_optional))
        answer = self.answer_q.get()
        if answer is InputBroker.EXIT:
            sys.exit()
        if answer is InputBroker.RESTART:
            raise RuntimeError()
        return answer

    def ask_yes_no(self, prompt):
        self.shared_q.put(("yesno", prompt))
        answer = self.answer_q.get()
        if answer is InputBroker.EXIT:
            sys.exit()
        if answer is InputBroker.RESTART:
            raise RuntimeError()
        return answer

    def emit_print(self, msg, colour, end):
        self.shared_q.put(("print", msg, colour, end))

    def emit_clear(self):
        self.shared_q.put(("clear", None))

    def emit_error(self, tb):
        self.shared_q.put(("error", tb))

    def emit_done(self):
        self.shared_q.put(("done", None))

    def send_answer(self, value):
        self.answer_q.put(value)

    def send_exit(self):
        self.answer_q.put(InputBroker.EXIT)

    def send_restart(self):
        self.answer_q.put(InputBroker.RESTART)


_current_broker: "InputBroker | None" = None


def set_current_broker(broker: "InputBroker") -> None:
    global _current_broker
    _current_broker = broker


def patched_get_input(input_type, prompt, ref, is_optional=False):
    if _current_broker is None:
        raise RuntimeError("No active GUI session")
    return _current_broker.ask(input_type, prompt, ref, is_optional)


def patched_input(prompt: str = "") -> str:
    if _current_broker is None:
        raise RuntimeError("No active GUI session")
    return _current_broker.ask_yes_no(prompt)


def patched_print_colour(msg, colour: str = "cyan", end: str = "\n") -> None:
    if _current_broker is not None:
        _current_broker.emit_print(str(msg), colour, end)


_patches_installed = False
verity_this = None  # set by install_patches()
_shape_key_order: "list[str] | None" = None  # set by install_patches()


def install_patches():
    """Imports the real tool and redirects its I/O primitives to our
    broker. Runs exactly once per process."""
    global _patches_installed, verity_this, _shape_key_order
    if _patches_installed:
        return verity_this

    # verity_this.py calls os.system("cls") once at import time; neutralise
    # that for the duration of the import so nothing flashes on screen.
    real_system = os.system
    os.system = lambda *a, **k: 0
    try:
        import verity_this as vt
    finally:
        os.system = real_system

    from src.io import read_inputs as read_inputs_module
    from src.algorithm import instructions as instructions_module
    from src.utils.constants import SHAPES

    read_inputs_module._get_input = patched_get_input
    read_inputs_module.print_colour = patched_print_colour
    instructions_module.print_colour = patched_print_colour
    vt.print_colour = patched_print_colour
    vt.input = patched_input

    verity_this = vt
    _shape_key_order = list(SHAPES.keys())
    _patches_installed = True
    return vt


def run_tool(broker: "InputBroker") -> None:
    """Thread target: replicates verity_this.py's own
    `if __name__ == "__main__":` loop, one on one."""
    try:
        run = True
        while run:
            try:
                run = verity_this.main()
            except RuntimeError:
                broker.emit_clear()
                run = True
    except SystemExit:
        pass
    except Exception:
        broker.emit_error(traceback.format_exc())
    finally:
        broker.emit_done()


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class VerityNativeGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Verity This!")
        self.root.geometry("920x680")
        self.root.minsize(680, 480)
        self.root.configure(bg=BG)

        self.shared_q: "queue.Queue" = queue.Queue()
        self.broker: "InputBroker | None" = None
        self.worker: "threading.Thread | None" = None
        self._current_input_type: "str | None" = None
        self._current_init: "str | None" = None
        self._current_io_context: "str | None" = None
        self._last_call_answer: "tuple | None" = None  # (input_type, io_context, value)
        self._last_question_shown: "tuple | None" = None  # (input_type, io_context)
        self._last_call_io_context: "str | None" = None
        self._history: "list[dict]" = []       # confirmed answers, in order, for Undo
        self._replay_queue: "list[dict]" = []   # answers still being auto-replayed after an Undo

        install_patches()
        self.always_on_top_var = tk.BooleanVar(value=True)
        self._build_ui()
        self.root.attributes("-topmost", self.always_on_top_var.get())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.root.after(30, self._poll_queue)
        self.start_new_session()

    # ---------------------------------------------------------------- UI --

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=10, pady=(10, 4))
        tk.Label(
            header, text="Verity This!", fg="#ffd54f", bg=BG,
            font=("Consolas", 16, "bold"),
        ).pack(side="left")
        self.status_var = tk.StringVar(value="Starting...")
        tk.Label(header, textvariable=self.status_var, fg="#9e9e9e", bg=BG, font=FONT).pack(
            side="right"
        )

        toolbar = tk.Frame(self.root, bg=BG)
        toolbar.pack(fill="x", padx=10)

        def toolbtn(parent, text, cmd, side="left"):
            b = tk.Button(
                parent, text=text, command=cmd, bg=BTN_BG, fg=FG_DEFAULT,
                activebackground="#444444", activeforeground=FG_DEFAULT,
                relief="flat", padx=8,
            )
            b.pack(side=side, padx=4)
            return b

        toolbtn(toolbar, "\u25B6 New Session", self.start_new_session)
        self.undo_btn = toolbtn(toolbar, "\u2B05 Undo", self.on_undo)
        self.exit_btn = toolbtn(toolbar, "\u2715 Exit tool", self.on_exit_tool)

        self.always_on_top_check = tk.Checkbutton(
            toolbar, text="Always on top", variable=self.always_on_top_var,
            command=self.on_toggle_always_on_top,
            bg=BG, fg=FG_DEFAULT, selectcolor=BTN_BG, activebackground=BG,
            activeforeground=FG_DEFAULT, relief="flat",
        )
        self.always_on_top_check.pack(side="left", padx=4)

        self.output = scrolledtext.ScrolledText(
            self.root, wrap="word", bg=BG, fg=FG_DEFAULT, insertbackground=FG_DEFAULT,
            font=FONT, state="disabled", relief="flat", padx=10, pady=8, height=16,
        )
        self.output.pack(fill="both", expand=True, padx=10, pady=(8, 4))
        for name, hexcolor in COLOUR_NAME_TO_HEX.items():
            if hexcolor:
                self.output.tag_configure(name, foreground=hexcolor)
        self.output.tag_configure("echo", foreground="#ffffff", font=FONT_BOLD)
        self.output.tag_configure("call_echo", foreground=COLOUR_NAME_TO_HEX["green"], font=FONT_BOLD)
        self.output.tag_configure("system", foreground="#757575", font=("Consolas", 10, "italic"))

        question_panel = tk.Frame(self.root, bg=PANEL_BG)
        question_panel.pack(fill="x", padx=10, pady=(0, 10))

        self.question_label = tk.Label(
            question_panel, text="Starting...", fg="#ffd54f", bg=PANEL_BG,
            font=FONT_BOLD, anchor="w", justify="left", wraplength=860,
        )
        self.question_label.pack(fill="x", padx=10, pady=(8, 4))

        self.input_buttons_frame = tk.Frame(question_panel, bg=PANEL_BG)
        self.input_buttons_frame.pack(fill="x", padx=10, pady=(0, 10))

    # ------------------------------------------------------------ session --

    def start_new_session(self, reset_history: bool = True) -> None:
        if self.worker and self.worker.is_alive() and self.broker:
            self.broker.send_exit()
            self.worker.join(timeout=1.0)

        self._clear_output()
        self._clear_input_frame()
        self.question_label.config(text="Starting...")
        self.status_var.set("Running")
        self._set_session_buttons_enabled(True)
        self._current_input_type = None
        self._current_init = None
        self._current_io_context = None
        self._last_call_answer = None
        self._last_call_io_context = None
        self._last_question_shown = None
        self._replay_queue = []
        if reset_history:
            self._history = []
        self._update_undo_button_state()

        self.shared_q = queue.Queue()
        self.broker = InputBroker(self.shared_q)
        set_current_broker(self.broker)

        self.worker = threading.Thread(target=run_tool, args=(self.broker,), daemon=True)
        self.worker.start()

    def on_undo(self) -> None:
        if not self._history:
            return
        target_history = self._history[:-1]
        self._start_replay(target_history)

    def _start_replay(self, target_history: "list[dict]") -> None:
        if self.worker and self.worker.is_alive() and self.broker:
            self.broker.send_exit()
            self.worker.join(timeout=1.0)

        self._clear_output()
        self._clear_input_frame()
        self.question_label.config(text="Replaying previous steps...")
        self.status_var.set("Replaying...")
        self._set_session_buttons_enabled(True)
        self._current_input_type = None
        self._current_init = None
        self._current_io_context = None
        self._last_call_answer = None
        self._last_call_io_context = None
        self._last_question_shown = None
        self._history = list(target_history)
        self._replay_queue = list(target_history)
        self._update_undo_button_state()

        self.shared_q = queue.Queue()
        self.broker = InputBroker(self.shared_q)
        set_current_broker(self.broker)

        self.worker = threading.Thread(target=run_tool, args=(self.broker,), daemon=True)
        self.worker.start()

    def _update_undo_button_state(self) -> None:
        self.undo_btn.config(state="normal" if self._history else "disabled")

    def on_exit_tool(self) -> None:
        self.on_close()

    def _set_session_buttons_enabled(self, enabled: bool) -> None:
        self.exit_btn.config(state="normal" if enabled else "disabled")

    # ------------------------------------------------------------- queue --

    def _poll_queue(self) -> None:
        try:
            while True:
                item = self.shared_q.get_nowait()
                kind = item[0]
                if kind == "print":
                    _, msg, colour, end = item
                    self._handle_print(msg, colour, end)
                elif kind == "question":
                    _, input_type, prompt, ref, is_optional = item
                    self._show_question(input_type, prompt, ref, is_optional)
                elif kind == "yesno":
                    _, prompt = item
                    self._show_yesno(prompt)
                elif kind == "clear":
                    self._clear_output()
                elif kind == "error":
                    _, tb = item
                    self._append_log("\n[Unexpected error -- session ended]\n" + tb + "\n", "red")
                elif kind == "done":
                    self._on_session_done()
        except queue.Empty:
            pass
        self.root.after(30, self._poll_queue)

    def _handle_print(self, msg, colour, end) -> None:
        if msg.strip() in SUPPRESSED_INTRO_LINES:
            return
        if colour == "green":
            m = AUTOFILL_RE.search(msg)
            if m:
                side_text, value = m.group(1), m.group(2)
                io_context = "inside" if side_text == "Inside wall" else "outside"
                label = body_2d_label(value) if io_context == "inside" else BODY_LABELS.get(value, value)
                short = short_prompt_label("r", io_context)
                self._append_log(f"> {short}: {label} <- (auto-filled)\n", "cyan")
                self._last_call_io_context = io_context
                return
        self._append_log(msg + end, colour)

    def _on_session_done(self) -> None:
        self._clear_input_frame()
        self.question_label.config(text='Session ended -- click "New Session" to run it again.')
        self.status_var.set("Session ended")
        self._set_session_buttons_enabled(False)

    # ------------------------------------------------------------- input --

    def _show_question(self, input_type, prompt, ref, is_optional) -> None:
        previous_question = self._last_question_shown
        self._current_input_type = input_type
        self._current_io_context = "inside" if "Inside" in prompt else "outside"
        self._last_question_shown = (input_type, self._current_io_context)
        self._clear_input_frame()

        if input_type in ("l", "m", "r"):
            if self._last_call_io_context == "inside" and self._current_io_context == "outside":
                self._append_log("\n", None)
            self._last_call_io_context = self._current_io_context

        if self._replay_queue and self._replay_queue[0]["input_type"] == input_type:
            entry = self._replay_queue.pop(0)
            self.question_label.config(
                text=f"Replaying previous steps... ({len(self._replay_queue)} left)"
            )
            self._finalize_answer(entry["value"], entry.get("label"))
            return
        if self._replay_queue:
            # Defensive: the recorded history no longer matches what the
            # (deterministic) tool is actually asking -- abort the replay
            # rather than risk feeding a wrong answer, and let the rest of
            # this and all further questions be asked live instead.
            self._replay_queue = []

        required_letter = required_init_letter(input_type, self._current_init)
        label_text = clean_prompt(prompt)
        if required_letter:
            label_text += f"  (must contain '{required_letter}')"
        self.question_label.config(text=label_text)

        if input_type == "init":
            options = [(p.upper(), p) for p in INIT_OPTIONS]
        elif input_type in ("l", "m", "r") and self._current_io_context == "inside":
            options = [(body_2d_label(k), k) for k in ref.keys()]
        else:
            label_map = LABEL_MAPS.get(input_type, {})
            options = [
                (label_map.get(k, str(k).replace("_", " ").capitalize()), k)
                for k in ref.keys()
            ]

        if is_optional:
            options.append(("Not specified / skip", None))

        disabled_values = compute_disabled_values(
            input_type, options, required_letter, self._current_init,
            self._current_io_context, self._last_call_answer, _shape_key_order,
            previous_question,
        )

        self._render_option_buttons(options, disabled_values)

    def _show_yesno(self, prompt) -> None:
        self._current_input_type = "yesno"
        self._last_question_shown = ("yesno", self._current_io_context)
        self._clear_input_frame()

        if self._replay_queue and self._replay_queue[0]["input_type"] == "yesno":
            entry = self._replay_queue.pop(0)
            self.question_label.config(
                text=f"Replaying previous steps... ({len(self._replay_queue)} left)"
            )
            self._finalize_answer(entry["value"], entry.get("label"))
            return
        if self._replay_queue:
            self._replay_queue = []

        self.question_label.config(text=clean_prompt(prompt))
        options = [("Yes, restart", "y"), ("No, end session", "n")]
        self._render_option_buttons(options)

    def _render_option_buttons(self, options, disabled_values=frozenset()) -> None:
        max_len = max((len(lbl) for lbl, _ in options), default=10)
        cols = 2 if max_len > 16 else 3
        cols = max(1, min(cols, len(options)))

        for i, (label, value) in enumerate(options):
            btn = tk.Button(
                self.input_buttons_frame, text=label, anchor="w",
                bg=BTN_BG, fg=FG_DEFAULT, disabledforeground="#5a5a5a",
                activebackground=BTN_ACTIVE_BG, activeforeground="#0a0a0a",
                relief="flat", padx=10, pady=8,
                state="disabled" if value in disabled_values else "normal",
                command=lambda v=value, l=label: self._answer(v, l),
            )
            btn.grid(row=i // cols, column=i % cols, padx=4, pady=4, sticky="ew")

        for c in range(cols):
            self.input_buttons_frame.grid_columnconfigure(c, weight=1)

    def _answer(self, value, display_label=None) -> None:
        self._history.append({
            "input_type": self._current_input_type,
            "value": value,
            "label": display_label,
        })
        self._update_undo_button_state()

        if self._current_input_type == "yesno" and value == "y":
            # "Yes, restart" at the very end of a playthrough now behaves
            # exactly like clicking "New Session": a full reset (log,
            # tracked state, fresh worker thread) instead of looping back
            # inside the same thread, which left the log and internal
            # state trackers (e.g. the last answered call) stale across
            # playthroughs. History is kept (not reset) so Undo can still
            # step back across the restart boundary.
            self.start_new_session(reset_history=False)
            return

        if self._current_input_type == "yesno" and value == "n":
            # "No, end session" now closes the whole app (same as the
            # window's X button / "Exit Tool"), instead of just ending the
            # worker thread and leaving an idle window behind.
            if self.broker:
                self.broker.send_answer("n")
            self.root.destroy()
            return

        self._finalize_answer(value, display_label)

    def _finalize_answer(self, value, display_label=None) -> None:
        """Core 'send this answer onward' logic, shared by live button
        clicks (via _answer) and by auto-replayed history entries after an
        Undo (via _show_question/_show_yesno) -- so a replayed transcript
        looks identical to the original one."""
        if display_label:
            short = short_prompt_label(self._current_input_type, self._current_io_context)
            tag = "call_echo" if self._current_input_type in ("l", "m", "r") else "echo"
            self._append_log(f"> {short}: {display_label}\n", tag)
        if self._current_input_type == "self_pos":
            self._append_log("\n", None)
        if self._current_input_type == "init":
            self._current_init = value
        if self._current_input_type in ("l", "m", "r"):
            self._last_call_answer = (self._current_input_type, self._current_io_context, value)
        self._clear_input_frame()
        self.question_label.config(text="Waiting for the tool...")
        if self.broker:
            self.broker.send_answer(value)

    def _clear_input_frame(self) -> None:
        for child in self.input_buttons_frame.winfo_children():
            child.destroy()

    # ------------------------------------------------------------ output --

    def _append_log(self, text, colour_name) -> None:
        tag = colour_name if colour_name in VALID_LOG_TAGS else None
        self.output.configure(state="normal")
        if tag:
            self.output.insert("end", text, tag)
        else:
            self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def _clear_output(self) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    # -------------------------------------------------------------- misc --

    def on_toggle_always_on_top(self) -> None:
        self.root.attributes("-topmost", self.always_on_top_var.get())

    def on_close(self) -> None:
        if self.broker:
            self.broker.send_exit()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    VerityNativeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
