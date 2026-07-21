
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
