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

import json
import os
import queue
import re
import sys
import threading
import traceback
import tkinter as tk
from tkinter import scrolledtext, ttk


# ---------------------------------------------------------------------------
# Make sure "import verity_this" / "import src...." resolves regardless of
# the current working directory.
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


# ---------------------------------------------------------------------------
# Visual style -- a small set of named themes, switchable at runtime from
# the "Theme" selector in the header. Every theme has the same keys, so
# _build_ui / _render_option_buttons / _apply_theme never special-case a
# particular theme's shape -- only its colour values differ.
# ---------------------------------------------------------------------------

FONT = ("Consolas", 11)
FONT_BOLD = ("Consolas", 11, "bold")

THEMES = {
    "Default": {
        "bg": "#1e1e1e",
        "panel_bg": "#242424",
        "fg": "#e0e0e0",
        "btn_bg": "#333333",
        "btn_active_bg": "#4fa8ff",
        "btn_active_fg": "#0a0a0a",
        "disabled_fg": "#5a5a5a",
        "toolbar_active_bg": "#444444",
        "title_fg": "#ffd54f",
        "status_fg": "#9e9e9e",
        "question_fg": "#ffd54f",
        "echo_fg": "#ffffff",
        "system_fg": "#757575",
        # Mirrors src/utils/constants.py COLOURS -- print_colour receives
        # these names directly (no ANSI parsing needed, unlike a subprocess
        # wrapper).
        "colours": {
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
        },
        "texture": None,
    },
    "Solarized Dark": {
        "bg": "#002b36",
        "panel_bg": "#073642",
        "fg": "#93a1a1",
        "btn_bg": "#073642",
        "btn_active_bg": "#268bd2",
        "btn_active_fg": "#00212b",
        "disabled_fg": "#3a5a63",
        "toolbar_active_bg": "#0e4a58",
        "title_fg": "#b58900",
        "status_fg": "#586e75",
        "question_fg": "#cb4b16",
        "echo_fg": "#eee8d5",
        "system_fg": "#586e75",
        "colours": {
            "default": None,
            "lightred": "#dc322f",
            "green": "#859900",
            "yellow": "#b58900",
            "blue": "#268bd2",
            "purple": "#d33682",
            "cyan": "#2aa198",
            "grey": "#586e75",
            "red": "#dc322f",
            "heavygreen": "#859900",
        },
        "texture": {"kind": "spectrum", "colours": [
            "#b58900", "#cb4b16", "#dc322f", "#d33682",
            "#6c71c4", "#268bd2", "#2aa198", "#859900",
        ]},
    },
    "Warm Paper": {
        "bg": "#f5ecd9",
        "panel_bg": "#ece0c8",
        "fg": "#3b2f2f",
        "btn_bg": "#e4d5b7",
        "btn_active_bg": "#c97b4a",
        "btn_active_fg": "#fff8ec",
        "disabled_fg": "#b0a48a",
        "toolbar_active_bg": "#d8c49e",
        "title_fg": "#8a5a2b",
        "status_fg": "#7a6a55",
        "question_fg": "#a13d2b",
        "echo_fg": "#2b2b2b",
        "system_fg": "#7a6a55",
        "colours": {
            "default": None,
            "lightred": "#c0392b",
            "green": "#4e7a33",
            "yellow": "#b8860b",
            "blue": "#2b6cb0",
            "purple": "#7b4397",
            "cyan": "#1f7a7a",
            "grey": "#6b6252",
            "red": "#a83232",
            "heavygreen": "#2f5d1f",
        },
        "texture": {"kind": "rule", "colour": "#c9b791"},
    },
    "Neon Cyberpunk": {
        "bg": "#0a0a12",
        "panel_bg": "#12121e",
        "fg": "#d6d6f5",
        "btn_bg": "#1b1b2e",
        "btn_active_bg": "#ff2fd0",
        "btn_active_fg": "#0a0a12",
        "disabled_fg": "#3a3a52",
        "toolbar_active_bg": "#2a2a44",
        "title_fg": "#00f0ff",
        "status_fg": "#7a7a9a",
        "question_fg": "#ff2fd0",
        "echo_fg": "#ffffff",
        "system_fg": "#7a7a9a",
        "colours": {
            "default": None,
            "lightred": "#ff5c8a",
            "green": "#39ff88",
            "yellow": "#faff00",
            "blue": "#3ba7ff",
            "purple": "#b026ff",
            "cyan": "#00f0ff",
            "grey": "#8888aa",
            "red": "#ff2b4e",
            "heavygreen": "#00ff9d",
        },
        "texture": {"kind": "scanline", "colour": "#16162a", "accent": "#00f0ff"},
    },
}

# Every Text-widget tag actually configured in _build_ui: the colour tags
# with a real hex value, plus the two special tags ("default" has no hex
# and is therefore never configured as a tag -- it just means "no tag").
# All themes share the same colour *names*, so any theme's dict will do.
VALID_LOG_TAGS = {
    name for name, hexcolor in THEMES["Default"]["colours"].items() if hexcolor
} | {"echo", "system", "call_echo"}

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


# ---------------------------------------------------------------------------
# Language support -- every piece of GUI-owned text (chrome, questions,
# option labels, and the scrolling log) is looked up from one of the
# language dictionaries in src/utils/constants.py rather than hard-coded in
# English, so switching the "Language" dropdown reaches every visible
# panel. DEFAULT_LANGUAGE (in that file) is rewritten in place by
# persist_default_language() whenever the dropdown changes, so the next run
# of this script starts in that language. DEFAULT_THEME works the same way
# for the "Theme" dropdown, via persist_default_theme().
# ---------------------------------------------------------------------------

from src.utils import constants as _constants_module
from src.utils.constants import (
    DEFAULT_LANGUAGE, LANGUAGE_NAMES, UI_TEXT, QUESTION_PROMPTS,
    MODE_LABELS, N_STRAT_LABELS, POSITION_LABELS, NUM_DOUBLES_LABELS,
    BODY_LABELS, SHAPE_2D_NAMES, SHORT_PROMPT_LABELS, FIELD_SHORT_NAME,
    POS_ADV_DE, DEFAULT_THEME,
)

def _persist_default_constant(const_name: str, value: str) -> None:
    """Rewrites a `NAME = "..."` constant in src/utils/constants.py in
    place, so the next `python gui_native.py` run starts with `value`
    instead of whatever that constant used to default to."""
    try:
        path = os.path.abspath(_constants_module.__file__)
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        pattern = re.compile(rf'^{re.escape(const_name)} = ".*"$', re.MULTILINE)
        new_source, count = pattern.subn(f'{const_name} = "{value}"', source, count=1)
        if count and new_source != source:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_source)
    except OSError:
        pass


# A PyInstaller build (`pyinstaller gui_native.py -F --windowed`) has no
# writable copy of constants.py to rewrite: -F re-extracts the bundled
# sources into a fresh temp folder (sys._MEIPASS) on every launch, so any
# edit made there is gone the moment the .exe exits, and _persist_default_
# constant()'s open(path, "w") either silently no-ops (caught OSError) or
# edits a copy nobody will ever read again. When frozen, persistence
# instead goes through a small JSON file in the user's per-user app-data
# folder, which -- unlike the temp extraction folder -- actually survives
# between runs of the .exe.

def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _settings_file_path() -> str:
    base = os.getenv("APPDATA") or os.path.expanduser("~")
    settings_dir = os.path.join(base, "VerityThis")
    os.makedirs(settings_dir, exist_ok=True)
    return os.path.join(settings_dir, "gui_settings.json")


def _load_persisted_settings() -> dict:
    """Only meaningful for a frozen build -- returns {} when running from
    source, so callers naturally fall back to the DEFAULT_* constants."""
    if not _is_frozen():
        return {}
    try:
        with open(_settings_file_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_persisted_setting(key: str, value: str) -> None:
    settings = _load_persisted_settings()
    settings[key] = value
    try:
        with open(_settings_file_path(), "w", encoding="utf-8") as f:
            json.dump(settings, f)
    except OSError:
        pass


def persist_default_language(lang_code: str) -> None:
    """Rewrites DEFAULT_LANGUAGE so the next run starts in the language
    just picked from the dropdown, instead of always resetting to
    English. In a frozen .exe, saves to the per-user settings file
    instead (see _save_persisted_setting)."""
    if _is_frozen():
        _save_persisted_setting("language", lang_code)
    else:
        _persist_default_constant("DEFAULT_LANGUAGE", lang_code)


def persist_default_theme(theme_name: str) -> None:
    """Rewrites DEFAULT_THEME so the next run starts with the theme just
    picked from the dropdown, instead of always resetting to "Default".
    In a frozen .exe, saves to the per-user settings file instead (see
    _save_persisted_setting)."""
    if _is_frozen():
        _save_persisted_setting("theme", theme_name)
    else:
        _persist_default_constant("DEFAULT_THEME", theme_name)


def body_2d_label(body_key: str, lang: str) -> str:
    names = SHAPE_2D_NAMES[lang]
    return " + ".join(names.get(ch, ch) for ch in body_key)


INIT_OPTIONS = ["cst", "cts", "sct", "stc", "tcs", "tsc"]


def label_maps_for(lang: str) -> dict:
    return {
        "mode": MODE_LABELS[lang],
        "n_strat": N_STRAT_LABELS[lang],
        "self_pos": POSITION_LABELS[lang],
        "number_of_doubles": NUM_DOUBLES_LABELS[lang],
        "l": BODY_LABELS[lang],
        "m": BODY_LABELS[lang],
        "r": BODY_LABELS[lang],
    }


def short_prompt_label(input_type: str, io_context: "str | None", lang: str) -> str:
    if input_type in FIELD_SHORT_NAME[lang]:
        side = UI_TEXT[lang]["inside_word"] if io_context == "inside" else UI_TEXT[lang]["outside_word"]
        return f"{side} {FIELD_SHORT_NAME[lang][input_type]}"
    return SHORT_PROMPT_LABELS[lang].get(input_type, str(input_type).replace("_", " ").title())


# ---------------------------------------------------------------------------
# Translation of the free-form text the underlying tool prints via
# print_colour (round headers, dunk instructions, validation errors, the
# closing thank-you message, ...). The tool itself always emits English --
# translation happens here, as a small set of regex substitutions covering
# every phrase actually produced by verity_this.py / src/algorithm/
# instructions.py / src/io/read_inputs.py, applied right before the text is
# appended to the log.
# ---------------------------------------------------------------------------

_LOG_TRANSLATIONS_DE = [
    (re.compile(r'\bRound (\d+)\b'), lambda m: f"Runde {m.group(1)}"),
    (re.compile(r'Outside steps:'), lambda m: "Schritte außen:"),
    (re.compile(r'Inside steps:'), lambda m: "Schritte innen:"),
    (re.compile(r'\bInside (left|middle|right): Wait until partners are ready\.\.\.'),
     lambda m: f"Innen {POS_ADV_DE[m.group(1)]}: Warte, bis die Partner bereit sind..."),
    (re.compile(r'\bWait until partners are ready\.\.\.'),
     lambda m: "Warte, bis die Partner bereit sind..."),
    (re.compile(r'\bInside (left|middle|right): Dunk (\w+) on the (left|middle|right|outside) statue'),
     lambda m: f"Innen {POS_ADV_DE[m.group(1)]}: {m.group(2)} auf die Statue {POS_ADV_DE[m.group(3)]}"),
    (re.compile(r'\bOutside: Dunk (\w+) on the (left|middle|right|outside) statue'),
     lambda m: f"Außen: {m.group(1)} auf die Statue {POS_ADV_DE[m.group(2)]}"),
    (re.compile(r'\bDunk (\w+) on the (left|middle|right|outside) statue'),
     lambda m: f"{m.group(1)} auf die Statue {POS_ADV_DE[m.group(2)]}"),
    (re.compile(r'Thank you for using Verity This!'),
     lambda m: "Danke, dass du Verity This! benutzt hast!"),
    (re.compile(r'Feel free to leave a \*star\* and share the GitHub repo'),
     lambda m: "Gib gerne einen *Star* und teile das GitHub-Repo"),
    (re.compile(r'In normal mode, a position has to be specified\.'),
     lambda m: "Im Normal-Modus muss eine Position angegeben werden."),
    (re.compile(r'(Outside statue|Inside wall) (left|middle|right) call must contain (\w) at least once\.'),
     lambda m: (f"Der {'äußere' if m.group(1) == 'Outside statue' else 'innere'} Ruf "
                f"{POS_ADV_DE[m.group(2)]} muss {m.group(3)} mindestens einmal enthalten.")),
    (re.compile(r'(Outside|Inside) inputs invalid\.'),
     lambda m: f"{'Außen' if m.group(1) == 'Outside' else 'Innen'}-Eingaben ungültig."),
    (re.compile(r'All called symbols have to occur at least once per side\.'),
     lambda m: "Alle gerufenen Symbole müssen pro Seite mindestens einmal vorkommen."),
    (re.compile(r'Symbols can occur at most twice in total\.'),
     lambda m: "Symbole dürfen insgesamt höchstens zweimal vorkommen."),
    (re.compile(r'The called symbol has to occur at least once per side\.'),
     lambda m: "Das gerufene Symbol muss pro Seite mindestens einmal vorkommen."),
    (re.compile(r'The given call is doubled, but num_doubles = (\d+) was given which is not possible then\.'),
     lambda m: (f"Der angegebene Ruf ist gedoppelt, aber num_doubles = {m.group(1)} wurde angegeben, "
                f"was dann nicht möglich ist.")),
    (re.compile(r'The given call is not doubled, but num_doubles = (\d+) was given which is not possible then\.'),
     lambda m: (f"Der angegebene Ruf ist nicht gedoppelt, aber num_doubles = {m.group(1)} wurde angegeben, "
                f"was dann nicht möglich ist.")),
]


def translate_log_text(text: str, lang: str) -> str:
    if lang == "en":
        return text
    for pattern, repl in _LOG_TRANSLATIONS_DE:
        text = pattern.sub(repl, text)
    return text

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
                            previous_question=None, current_mode=None):
    """Pure decision logic for which option *values* should be disabled for
    a given question. Deliberately does nothing (returns an empty set) for
    any input_type other than the body-call fields 'l', 'm', 'r',
    'number_of_doubles', and the 'self_pos' skip option -- mode, n_strat,
    and init are never touched here.

    previous_question, if given, is the (input_type, io_context) of the
    question shown immediately before this one -- used to make sure a
    'left' answer is only treated as feeding into 'middle' when it was
    truly asked right before it in the same call-group, not left over from
    an earlier round's single-position call (e.g. 'left' in round 1
    followed by an unrelated 'middle' in round 2)."""
    if input_type == "self_pos":
        # Mirrors verity_this.py's own _await_input check: in 'normal' mode
        # a position is mandatory, so 'Not specified / skip' would just
        # bounce back with a red error -- disable it up front instead.
        if current_mode == "normal":
            return {value for _, value in options if value is None}
        return set()

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

        self.shared_q: "queue.Queue" = queue.Queue()
        self.broker: "InputBroker | None" = None
        self.worker: "threading.Thread | None" = None
        self._current_input_type: "str | None" = None
        self._current_init: "str | None" = None
        self._current_mode: "str | None" = None
        self._current_io_context: "str | None" = None
        self._last_call_answer: "tuple | None" = None  # (input_type, io_context, value)
        self._last_question_shown: "tuple | None" = None  # (input_type, io_context)
        self._last_call_io_context: "str | None" = None
        self._history: "list[dict]" = []       # confirmed answers, in order, for Undo
        self._replay_queue: "list[dict]" = []   # answers still being auto-replayed after an Undo
        self._last_options: "list | None" = None       # options shown by the current
        self._last_disabled: "frozenset" = frozenset()  # question, if any -- for theme re-render
        self._current_ref_keys: "list | None" = None    # value keys of the current question's
        self._current_is_optional: bool = False          # options -- for language re-render
        self._required_letter: "str | None" = None
        self._status_key: str = "starting"               # which UI_TEXT entry status_var shows
        self._question_static_key = None                 # non-interactive question_label state:
                                                           # a UI_TEXT key, or ("replaying_n", n)

        install_patches()
        persisted = _load_persisted_settings()  # {} unless running frozen
        self._theme_name = persisted.get("theme") if persisted.get("theme") in THEMES else DEFAULT_THEME
        self._theme = THEMES[self._theme_name]
        self._lang = persisted.get("language") if persisted.get("language") in LANGUAGE_NAMES else DEFAULT_LANGUAGE
        self._ttk_style = ttk.Style()
        try:
            self._ttk_style.theme_use("clam")  # only 'clam' honours custom Combobox colours
        except tk.TclError:
            pass
        self.always_on_top_var = tk.BooleanVar(value=True)
        self._build_ui()
        self._apply_theme(self._theme_name)
        self.root.attributes("-topmost", self.always_on_top_var.get())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.root.after(30, self._poll_queue)
        self.start_new_session()

    # ---------------------------------------------------------------- UI --

    def _build_ui(self) -> None:
        theme = self._theme

        self.header = tk.Frame(self.root, bg=theme["bg"])
        self.header.pack(fill="x", padx=10, pady=(10, 4))
        self.title_label = tk.Label(
            self.header, text="Verity This!", font=("Consolas", 16, "bold"),
        )
        self.title_label.pack(side="left")

        # Packed right-to-left so the theme selector lands in the true
        # top-right corner, with the language selector, then the status
        # text, just to its left.
        self.theme_frame = tk.Frame(self.header)
        self.theme_caption = tk.Label(self.theme_frame, text=UI_TEXT[self._lang]["theme_caption"], font=FONT)
        self.theme_caption.pack(side="left", padx=(0, 4))
        self.theme_var = tk.StringVar(value=self._theme_name)
        self.theme_combo = ttk.Combobox(
            self.theme_frame, textvariable=self.theme_var, values=list(THEMES.keys()),
            state="readonly", width=15, font=FONT, style="Themed.TCombobox",
        )
        self.theme_combo.pack(side="left")
        self.theme_combo.bind("<<ComboboxSelected>>", self._on_theme_selected)
        self.theme_frame.pack(side="right")

        self.lang_frame = tk.Frame(self.header)
        self.language_caption = tk.Label(self.lang_frame, text=UI_TEXT[self._lang]["language_caption"], font=FONT)
        self.language_caption.pack(side="left", padx=(0, 4))
        self.lang_var = tk.StringVar(value=LANGUAGE_NAMES[self._lang])
        self.lang_combo = ttk.Combobox(
            self.lang_frame, textvariable=self.lang_var,
            values=list(LANGUAGE_NAMES.values()), state="readonly", width=10,
            font=FONT, style="Themed.TCombobox",
        )
        self.lang_combo.pack(side="left")
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_selected)
        self.lang_frame.pack(side="right", padx=(0, 10))

        self.status_var = tk.StringVar(value=UI_TEXT[self._lang]["starting"])
        self.status_label = tk.Label(self.header, textvariable=self.status_var, font=FONT)
        self.status_label.pack(side="right", padx=(0, 10))

        # Decorative texture strip -- purely cosmetic, lives in its own
        # fixed-height canvas so it never overlaps any text and switching
        # themes never causes the rest of the layout to jump.
        self.texture_canvas = tk.Canvas(self.root, height=8, highlightthickness=0)
        self.texture_canvas.pack(fill="x", padx=10)
        self.texture_canvas.bind("<Configure>", self._draw_texture)

        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(fill="x", padx=10, pady=(4, 0))

        def toolbtn(parent, text, cmd, side="left"):
            b = tk.Button(parent, text=text, command=cmd, relief="flat", padx=8)
            b.pack(side=side, padx=4)
            return b

        self.new_session_btn = toolbtn(self.toolbar, UI_TEXT[self._lang]["new_session_btn"], self.start_new_session)
        self.undo_btn = toolbtn(self.toolbar, UI_TEXT[self._lang]["undo_btn"], self.on_undo)
        self.exit_btn = toolbtn(self.toolbar, UI_TEXT[self._lang]["exit_btn"], self.on_exit_tool)

        self.always_on_top_check = tk.Checkbutton(
            self.toolbar, text=UI_TEXT[self._lang]["always_on_top"], variable=self.always_on_top_var,
            command=self.on_toggle_always_on_top, relief="flat",
        )
        self.always_on_top_check.pack(side="left", padx=4)

        self.output = scrolledtext.ScrolledText(
            self.root, wrap="word", insertbackground=theme["fg"],
            font=FONT, state="disabled", relief="flat", padx=10, pady=8, height=16,
        )
        self.output.pack(fill="both", expand=True, padx=10, pady=(8, 4))

        self.question_panel = tk.Frame(self.root)
        self.question_panel.pack(fill="x", padx=10, pady=(0, 10))

        self.question_label = tk.Label(
            self.question_panel, text=UI_TEXT[self._lang]["starting"],
            font=FONT_BOLD, anchor="w", justify="left", wraplength=860,
        )
        self.question_label.pack(fill="x", padx=10, pady=(8, 4))

        self.input_buttons_frame = tk.Frame(self.question_panel)
        self.input_buttons_frame.pack(fill="x", padx=10, pady=(0, 10))

    # ----------------------------------------------------------- theming --

    def _draw_texture(self, event=None) -> None:
        canvas = self.texture_canvas
        theme = self._theme
        canvas.configure(bg=theme["bg"])
        canvas.delete("all")
        spec = theme.get("texture")
        if not spec:
            return
        w = canvas.winfo_width()
        if spec["kind"] == "spectrum":
            colours = spec["colours"]
            seg = max(1, w // len(colours))
            for i, colour in enumerate(colours):
                x1 = i * seg
                x2 = (i + 1) * seg if i < len(colours) - 1 else w
                canvas.create_rectangle(x1, 0, x2, 4, fill=colour, width=0)
        elif spec["kind"] == "rule":
            canvas.create_line(0, 0, w, 0, fill=spec["colour"], width=1)
            canvas.create_line(0, 2, w, 2, fill=spec["colour"], width=1)
        elif spec["kind"] == "scanline":
            for y in range(0, 6, 2):
                canvas.create_line(0, y, w, y, fill=spec["colour"], width=1)
            canvas.create_line(0, 7, w, 7, fill=spec["accent"], width=1)

    def _on_theme_selected(self, event=None) -> None:
        name = self.theme_var.get()
        self._apply_theme(name)
        persist_default_theme(name)

    def _on_language_selected(self, event=None) -> None:
        display_name = self.lang_var.get()
        lang = next(code for code, name in LANGUAGE_NAMES.items() if name == display_name)
        self._apply_language(lang)
        persist_default_language(lang)

    def _apply_theme(self, name: str) -> None:
        theme = THEMES[name]
        self._theme_name = name
        self._theme = theme
        self.theme_var.set(name)

        self.root.configure(bg=theme["bg"])
        self.header.configure(bg=theme["bg"])
        self.title_label.configure(fg=theme["title_fg"], bg=theme["bg"])
        self.theme_frame.configure(bg=theme["bg"])
        self.theme_caption.configure(fg=theme["status_fg"], bg=theme["bg"])
        self.lang_frame.configure(bg=theme["bg"])
        self.language_caption.configure(fg=theme["status_fg"], bg=theme["bg"])
        self.status_label.configure(fg=theme["status_fg"], bg=theme["bg"])

        self._ttk_style.configure(
            "Themed.TCombobox",
            fieldbackground=theme["btn_bg"], background=theme["btn_bg"],
            foreground=theme["fg"], arrowcolor=theme["fg"],
            selectbackground=theme["btn_bg"], selectforeground=theme["fg"],
        )
        self._ttk_style.map(
            "Themed.TCombobox",
            fieldbackground=[("readonly", theme["btn_bg"])],
            foreground=[("readonly", theme["fg"])],
        )
        self.root.option_add("*TCombobox*Listbox.background", theme["btn_bg"])
        self.root.option_add("*TCombobox*Listbox.foreground", theme["fg"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", theme["btn_active_bg"])

        self.toolbar.configure(bg=theme["bg"])
        for btn in (self.new_session_btn, self.undo_btn, self.exit_btn):
            btn.configure(
                bg=theme["btn_bg"], fg=theme["fg"],
                activebackground=theme["toolbar_active_bg"], activeforeground=theme["fg"],
            )
        self.always_on_top_check.configure(
            bg=theme["bg"], fg=theme["fg"], selectcolor=theme["btn_bg"],
            activebackground=theme["bg"], activeforeground=theme["fg"],
        )

        self.output.configure(bg=theme["bg"], fg=theme["fg"], insertbackground=theme["fg"])
        for cname, hexcolor in theme["colours"].items():
            if hexcolor:
                self.output.tag_configure(cname, foreground=hexcolor)
        self.output.tag_configure("echo", foreground=theme["echo_fg"], font=FONT_BOLD)
        self.output.tag_configure("call_echo", foreground=theme["colours"]["green"], font=FONT_BOLD)
        self.output.tag_configure("system", foreground=theme["system_fg"], font=("Consolas", 10, "italic"))

        self.question_panel.configure(bg=theme["panel_bg"])
        self.question_label.configure(fg=theme["question_fg"], bg=theme["panel_bg"])
        self.input_buttons_frame.configure(bg=theme["panel_bg"])

        self._draw_texture()

        if self._last_options is not None:
            options, disabled = self._last_options, self._last_disabled
            self._clear_input_frame()
            self._render_option_buttons(options, disabled)

    def _apply_language(self, lang: str) -> None:
        self._lang = lang
        self.lang_var.set(LANGUAGE_NAMES[lang])
        t = UI_TEXT[lang]

        self.theme_caption.configure(text=t["theme_caption"])
        self.language_caption.configure(text=t["language_caption"])
        self.new_session_btn.configure(text=t["new_session_btn"])
        self.undo_btn.configure(text=t["undo_btn"])
        self.exit_btn.configure(text=t["exit_btn"])
        self.always_on_top_check.configure(text=t["always_on_top"])

        self.status_var.set(t[self._status_key])
        self.question_label.config(text=self._question_label_text())

        if self._last_options is not None:
            if self._current_input_type == "yesno":
                options = [(t["yes_restart"], "y"), (t["no_end_session"], "n")]
            else:
                options = self._options_for(
                    self._current_input_type, self._current_io_context,
                    self._current_ref_keys, self._current_is_optional, lang,
                )
            disabled = self._last_disabled
            self._clear_input_frame()
            self._render_option_buttons(options, disabled)

    # -------------------------------------------------------------- text --

    def _build_question_prompt_text(self, input_type: str, io_context: "str | None", lang: str) -> str:
        qp = QUESTION_PROMPTS[lang]
        if input_type in ("l", "m", "r"):
            field = qp["field"][input_type]
            template = qp["call_inside"] if io_context == "inside" else qp["call_outside"]
            return template.format(field=field)
        if input_type == "self_pos":
            text = qp["self_pos"]
            if self._current_mode != "normal":
                text += qp["self_pos_optional_suffix"]
            return text
        return qp.get(input_type, "")

    def _question_label_text(self) -> str:
        lang = self._lang
        t = UI_TEXT[lang]
        if self._question_static_key is not None:
            key = self._question_static_key
            if isinstance(key, tuple) and key[0] == "replaying_n":
                return t["replaying_question_n"].format(n=key[1])
            return t[key]
        if self._current_input_type == "yesno":
            return QUESTION_PROMPTS[lang]["restart"]
        if self._current_input_type is not None:
            text = self._build_question_prompt_text(self._current_input_type, self._current_io_context, lang)
            if self._required_letter:
                text += t["must_contain"].format(letter=self._required_letter)
            return text
        return ""

    def _options_for(self, input_type, io_context, ref_keys, is_optional, lang) -> list:
        if input_type == "init":
            options = [(p.upper(), p) for p in INIT_OPTIONS]
        elif input_type in ("l", "m", "r") and io_context == "inside":
            options = [(body_2d_label(k, lang), k) for k in ref_keys]
        else:
            label_map = label_maps_for(lang).get(input_type, {})
            options = [
                (label_map.get(k, str(k).replace("_", " ").capitalize()), k)
                for k in ref_keys
            ]
        if is_optional:
            options.append((UI_TEXT[lang]["not_specified_skip"], None))
        return options

    # ------------------------------------------------------------ session --

    def start_new_session(self, reset_history: bool = True) -> None:
        if self.worker and self.worker.is_alive() and self.broker:
            self.broker.send_exit()
            self.worker.join(timeout=1.0)

        self._clear_output()
        self._clear_input_frame()
        self._question_static_key = "starting"
        self._status_key = "running"
        self.question_label.config(text=self._question_label_text())
        self.status_var.set(UI_TEXT[self._lang][self._status_key])
        self._set_session_buttons_enabled(True)
        self._current_input_type = None
        self._current_init = None
        self._current_mode = None
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
        self._question_static_key = "replaying_question"
        self._status_key = "replaying_status"
        self.question_label.config(text=self._question_label_text())
        self.status_var.set(UI_TEXT[self._lang][self._status_key])
        self._set_session_buttons_enabled(True)
        self._current_input_type = None
        self._current_init = None
        self._current_mode = None
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
                lang = self._lang
                label = body_2d_label(value, lang) if io_context == "inside" else BODY_LABELS[lang].get(value, value)
                short = short_prompt_label("r", io_context, lang)
                self._append_log(f"> {short}: {label}{UI_TEXT[lang]['auto_filled_suffix']}\n", "cyan")
                self._last_call_io_context = io_context
                return
        self._append_log(translate_log_text(msg, self._lang) + end, colour)

    def _on_session_done(self) -> None:
        self._clear_input_frame()
        self._question_static_key = "session_ended_msg"
        self._status_key = "session_ended_status"
        self.question_label.config(text=self._question_label_text())
        self.status_var.set(UI_TEXT[self._lang][self._status_key])
        self._set_session_buttons_enabled(False)

    # ------------------------------------------------------------- input --

    def _show_question(self, input_type, prompt, ref, is_optional) -> None:
        previous_question = self._last_question_shown
        self._current_input_type = input_type
        self._current_io_context = "inside" if "Inside" in prompt else "outside"
        self._current_ref_keys = list(ref.keys())
        self._current_is_optional = is_optional
        self._question_static_key = None
        self._last_question_shown = (input_type, self._current_io_context)
        self._clear_input_frame()

        if input_type in ("l", "m", "r"):
            if self._last_call_io_context == "inside" and self._current_io_context == "outside":
                self._append_log("\n", None)
            self._last_call_io_context = self._current_io_context

        if self._replay_queue and self._replay_queue[0]["input_type"] == input_type:
            entry = self._replay_queue.pop(0)
            self._question_static_key = ("replaying_n", len(self._replay_queue))
            self.question_label.config(text=self._question_label_text())
            self._finalize_answer(entry["value"], entry.get("label"))
            return
        if self._replay_queue:
            # Defensive: the recorded history no longer matches what the
            # (deterministic) tool is actually asking -- abort the replay
            # rather than risk feeding a wrong answer, and let the rest of
            # this and all further questions be asked live instead.
            self._replay_queue = []

        self._required_letter = required_init_letter(input_type, self._current_init)
        self.question_label.config(text=self._question_label_text())

        options = self._options_for(
            input_type, self._current_io_context, self._current_ref_keys,
            is_optional, self._lang,
        )

        disabled_values = compute_disabled_values(
            input_type, options, self._required_letter, self._current_init,
            self._current_io_context, self._last_call_answer, _shape_key_order,
            previous_question, self._current_mode,
        )

        self._render_option_buttons(options, disabled_values)

    def _show_yesno(self, prompt) -> None:
        self._current_input_type = "yesno"
        self._question_static_key = None
        self._last_question_shown = ("yesno", self._current_io_context)
        self._clear_input_frame()

        if self._replay_queue and self._replay_queue[0]["input_type"] == "yesno":
            entry = self._replay_queue.pop(0)
            self._question_static_key = ("replaying_n", len(self._replay_queue))
            self.question_label.config(text=self._question_label_text())
            self._finalize_answer(entry["value"], entry.get("label"))
            return
        if self._replay_queue:
            self._replay_queue = []

        self.question_label.config(text=self._question_label_text())
        options = [
            (UI_TEXT[self._lang]["yes_restart"], "y"),
            (UI_TEXT[self._lang]["no_end_session"], "n"),
        ]
        self._render_option_buttons(options)

    def _render_option_buttons(self, options, disabled_values=frozenset()) -> None:
        self._last_options = options
        self._last_disabled = disabled_values
        theme = self._theme
        max_len = max((len(lbl) for lbl, _ in options), default=10)
        cols = 2 if max_len > 16 else 3
        cols = max(1, min(cols, len(options)))

        for i, (label, value) in enumerate(options):
            btn = tk.Button(
                self.input_buttons_frame, text=label, anchor="w",
                bg=theme["btn_bg"], fg=theme["fg"], disabledforeground=theme["disabled_fg"],
                activebackground=theme["btn_active_bg"], activeforeground=theme["btn_active_fg"],
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
            short = short_prompt_label(self._current_input_type, self._current_io_context, self._lang)
            tag = "call_echo" if self._current_input_type in ("l", "m", "r") else "echo"
            self._append_log(f"> {short}: {display_label}\n", tag)
        if self._current_input_type == "self_pos":
            self._append_log("\n", None)
        if self._current_input_type == "init":
            self._current_init = value
        if self._current_input_type == "mode":
            self._current_mode = value
        if self._current_input_type in ("l", "m", "r"):
            self._last_call_answer = (self._current_input_type, self._current_io_context, value)
        self._clear_input_frame()
        self._question_static_key = "waiting_for_tool"
        self.question_label.config(text=self._question_label_text())
        if self.broker:
            self.broker.send_answer(value)

    def _clear_input_frame(self) -> None:
        for child in self.input_buttons_frame.winfo_children():
            child.destroy()
        self._last_options = None
        self._last_disabled = frozenset()

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
