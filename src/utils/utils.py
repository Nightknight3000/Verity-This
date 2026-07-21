from src.utils.constants import COLOURS


def print_colour(msg: str, colour: str = 'cyan', end: str = '\n') -> None:
    if colour in COLOURS.keys():
        print(f"\x1b[{COLOURS[colour]}m{msg}\x1b[0m", end=end)
    else:
        raise IOError("Invalid colour")
