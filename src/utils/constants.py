
MODES = {
    "normal": ["n", "norm", "normal"],
    "all_normal": ["a", "all", "14all", "all_normal", "normal_for_all"],
    "triumph": ["t", "tri", "triumph"],
    "challenge": ["c", "chall", "challenge"],
    "hard_challenge": ["hc", "ch", "hchall", "hard_challenge", "why"],
    "triumph+challenge": ["tc", "ct", "tri+chall", "triumph+challenge", "mindbend"],
    "triumph+hard_challenge": ["thc", "cht", "cth", "hct", "htc", "tch", "tri+hchall", "triumph+hard_challenge", "ineedweed"],
}

NUM_DOUBLES = {
    '0': ['0', 'zero', 'singles', 'None'],
    '1': ['1', 'one', 'one_dub'],
    '3': ['3', 'three', 'all', 'all_dub']
}


N_STRATS = {
    "double-up": ["d", "double", "double-up"],
    "speed": ["s", "speed"]
}


POSITIONS = {
    "outside": ["o", "out", "outside"],
    "left": ["l", "il", "left", "i-left", "inside l", "inside left"],
    "middle": ["m", "im", "mid", "middle", "i-middle", "inside m", "inside mid", "inside middle"],
    "right": ["r", "ir", "right", "i-right", "inside r", "inside right"]
}


SHAPES = {
    "s": ["s", "sq", "square"],
    "t": ["t", "tri", "triangle"],
    "c": ["c", "cir", "circle"]
}


BODIES = {
    "cc": ["cc", "sp", "sphere"],
    "ss": ["ss", "cu", "cube"],
    "tt": ["tt", "py", "pyramid"],
    "st": ["st", "ts", "pr", "prism"],
    "cs": ["sc", "cs", "cy", "cylinder"],
    "ct": ["tc", "ct", "co", "cone"]
}


SHAPE_TO_BODY = {
    "ss": "cube",
    "st": "prism",
    "sc": "cylinder",
    "ts": "prism",
    "tt": "pyramid",
    "tc": "cone",
    "cs": "cylinder",
    "ct": "cone",
    "cc": "sphere",
}


BODY_TO_SHAPE = {
    "cube": "ss",
    "prism": "st",
    "cylinder": "sc",
    "pyramid": "tt",
    "cone": "tc",
    "sphere": "cc",
}


COLOURS = {'default': 0,
           'lightred': 31,
           'green': 32,
           'yellow': 33,
           'blue': 34,
           'purple': 35,
           'cyan': 36,
           'grey': 90,
           'red': 91,
           'heavygreen': 92}


SKIP_EXCEPTED_TYPES = ["mode", "n_strat"]


# ---------------------------------------------------------------------------
# gui_native.py language support -- every piece of GUI-owned text (chrome,
# questions, option labels, and the scrolling log) is looked up from one of
# the dictionaries below rather than hard-coded in English, so switching the
# GUI's "Language" dropdown reaches every visible panel. DEFAULT_LANGUAGE is
# rewritten in place by gui_native.persist_default_language() whenever the
# dropdown changes, so the next run of the GUI starts in that language.
# ---------------------------------------------------------------------------

DEFAULT_LANGUAGE = "en"

LANGUAGE_NAMES = {
    "en": "English",
    "de": "Deutsch",
}

# gui_native.py theme support -- the actual colour values for each named
# theme live in gui_native.THEMES (visual styling, not GUI text), but the
# name of the theme to start in is kept here, next to DEFAULT_LANGUAGE, so
# gui_native.persist_default_theme() can rewrite it the same way whenever
# the "Theme" dropdown changes.
DEFAULT_THEME = "Default"

# GUI chrome -- toolbar/status/dropdown/button text that isn't sourced from
# the underlying tool at all.
UI_TEXT = {
    "en": {
        "theme_caption": "Theme:",
        "language_caption": "Language:",
        "new_session_btn": "▶ New Session",
        "undo_btn": "⬅ Undo",
        "exit_btn": "✕ Exit tool",
        "always_on_top": "Always on top",
        "starting": "Starting...",
        "running": "Running",
        "replaying_status": "Replaying...",
        "replaying_question": "Replaying previous steps...",
        "replaying_question_n": "Replaying previous steps... ({n} left)",
        "session_ended_status": "Session ended",
        "session_ended_msg": 'Session ended -- click "New Session" to run it again.',
        "waiting_for_tool": "Waiting for the tool...",
        "not_specified_skip": "Not specified / skip",
        "yes_restart": "Yes, restart",
        "no_end_session": "No, end session",
        "auto_filled_suffix": " <- (auto-filled)",
        "must_contain": "  (must contain '{letter}')",
        "inside_word": "Inside",
        "outside_word": "Outside",
    },
    "de": {
        "theme_caption": "Design:",
        "language_caption": "Sprache:",
        "new_session_btn": "▶ Neue Sitzung",
        "undo_btn": "⬅ Rückgängig",
        "exit_btn": "✕ Tool beenden",
        "always_on_top": "Immer im Vordergrund",
        "starting": "Wird gestartet...",
        "running": "Läuft",
        "replaying_status": "Wird wiederholt...",
        "replaying_question": "Vorherige Schritte werden wiederholt...",
        "replaying_question_n": "Vorherige Schritte werden wiederholt... (noch {n})",
        "session_ended_status": "Sitzung beendet",
        "session_ended_msg": 'Sitzung beendet -- klicke auf "Neue Sitzung", um erneut zu starten.',
        "waiting_for_tool": "Warte auf das Tool...",
        "not_specified_skip": "Nicht angegeben / überspringen",
        "yes_restart": "Ja, neu starten",
        "no_end_session": "Nein, Sitzung beenden",
        "auto_filled_suffix": " <- (automatisch ausgefüllt)",
        "must_contain": "  (muss '{letter}' enthalten)",
        "inside_word": "Innen",
        "outside_word": "Außen",
    },
}

# The fixed question prompts asked by src/io/read_inputs.py and
# verity_this.py, keyed by input_type rather than parsed out of the raw CLI
# prompt string -- far more robust than regexing translated text back out of
# English.
QUESTION_PROMPTS = {
    "en": {
        "mode": "Enter mode (n/a/t/c/tc/...)",
        "n_strat": "Is your team running the 'double-up'- or 'speed'-strat?",
        "init": "Enter init (ex. 'cst')",
        "self_pos": "Where are you currently (out/left/middle/right)?",
        "self_pos_optional_suffix": " [optional]",
        "number_of_doubles": "Total number of doubles inside",
        "call_outside": "Outside statue {field} (ex. 'cs')",
        "call_inside": "Inside wall {field} (ex. 'cs')",
        "field": {"l": "left", "m": "middle", "r": "right"},
        "restart": "Restart (y/N)?",
    },
    "de": {
        "mode": "Modus eingeben (n/a/t/c/tc/...)",
        "n_strat": "Spielt euer Team die 'Double-Up'- oder die 'Speed'-Strategie?",
        "init": "Init eingeben (z. B. 'cst')",
        "self_pos": "Wo befindest du dich gerade (out/left/middle/right)?",
        "self_pos_optional_suffix": " [optional]",
        "number_of_doubles": "Gesamtzahl der Doppel innen",
        "call_outside": "Äußere Statue {field} (z. B. 'cs')",
        "call_inside": "Innere Wand {field} (z. B. 'cs')",
        "field": {"l": "links", "m": "Mitte", "r": "rechts"},
        "restart": "Neu starten (j/N)?",
    },
}


# ---------------------------------------------------------------------------
# Friendly button labels for each dict above, keyed by input_type. Every
# dict below is keyed first by language, then by the same value keys the
# dicts above use -- only the *display* label changes with language, never
# the underlying value gui_native.py sends back to the tool.
# ---------------------------------------------------------------------------

MODE_LABELS = {
    "en": {
        "normal": "Normal",
        "all_normal": "All Normal",
        "triumph": "Triumph",
        "challenge": "Challenge",
        "hard_challenge": "Hard Challenge",
        "triumph+challenge": "Triumph + Challenge",
        "triumph+hard_challenge": "Triumph + Hard Challenge",
    },
    "de": {
        "normal": "Normal",
        "all_normal": "Alle normal",
        "triumph": "Triumph",
        "challenge": "Challenge",
        "hard_challenge": "Schwere Challenge",
        "triumph+challenge": "Triumph + Challenge",
        "triumph+hard_challenge": "Triumph + Schwere Challenge",
    },
}
N_STRAT_LABELS = {
    "en": {"double-up": "Double-Up", "speed": "Speed"},
    "de": {"double-up": "Double-Up", "speed": "Speed"},
}
POSITION_LABELS = {
    "en": {
        "outside": "Outside",
        "left": "Inside Left",
        "middle": "Inside Middle",
        "right": "Inside Right",
    },
    "de": {
        "outside": "Außen",
        "left": "Innen Links",
        "middle": "Innen Mitte",
        "right": "Innen Rechts",
    },
}
NUM_DOUBLES_LABELS = {
    "en": {"0": "0 (no doubles)", "1": "1 double", "3": "3 (all doubled)"},
    "de": {"0": "0 (keine Doppel)", "1": "1 Doppel", "3": "3 (alle gedoppelt)"},
}
BODY_LABELS = {
    "en": {
        "cc": "Sphere (cc)",
        "ss": "Cube (ss)",
        "tt": "Pyramid (tt)",
        "st": "Prism (st)",
        "cs": "Cylinder (cs)",
        "ct": "Cone (ct)",
    },
    "de": {
        "cc": "Kugel (cc)",
        "ss": "Würfel (ss)",
        "tt": "Pyramide (tt)",
        "st": "Prisma (st)",
        "cs": "Zylinder (cs)",
        "ct": "Kegel (ct)",
    },
}

# Inside walls show the 2D symbol pairs directly (unlike the outside
# statues, which show the corresponding 3D body) -- so 'l'/'m'/'r' options
# are labelled as a combination of their two 2D parts when io_context is
# "inside", instead of the 3D body name used for "outside".
SHAPE_2D_NAMES = {
    "en": {"c": "Circle", "s": "Square", "t": "Triangle"},
    "de": {"c": "Kreis", "s": "Quadrat", "t": "Dreieck"},
}

# Short prefixes used in the log to show which question an echoed answer
# belongs to, e.g. "> Mode: Normal" or "> Inside Left: Sphere (cc)".
SHORT_PROMPT_LABELS = {
    "en": {
        "mode": "Mode",
        "n_strat": "Strategy",
        "init": "Init",
        "self_pos": "Position",
        "number_of_doubles": "Doubles",
        "yesno": "Restart?",
    },
    "de": {
        "mode": "Modus",
        "n_strat": "Strategie",
        "init": "Init",
        "self_pos": "Position",
        "number_of_doubles": "Doppel",
        "yesno": "Neustart?",
    },
}
FIELD_SHORT_NAME = {
    "en": {"l": "Left", "m": "Middle", "r": "Right"},
    "de": {"l": "Links", "m": "Mitte", "r": "Rechts"},
}

# Position -> German adverb, used by gui_native.translate_log_text() to
# translate the free-form instruction text printed by the underlying tool
# (e.g. "Dunk cc on the left statue" -> "... auf die Statue links ...").
POS_ADV_DE = {"left": "links", "middle": "mitte", "right": "rechts", "outside": "außen"}
