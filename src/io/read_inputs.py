import sys
from typing import Optional

from src.utils.constants import *
from src.utils.utils import print_colour


def get_mode() -> Optional[str]:
    return _get_input(
        "mode",
        "Enter mode (n/a/t/c/tc/...): ",
        MODES
    )


def get_normal_strat() -> Optional[str]:
    return _get_input(
        "n_strat",
        "Is your team running the 'double-up'- or 'speed'-strat?: ",
        N_STRATS
    )


def get_init() -> Optional[str]:
    return _get_input(
        "init",
        "\tEnter init (ex. 'cst'): ",
        SHAPES
    )


def get_self_pos(mode: Optional[str] = None) -> Optional[str]:
    return _get_input(
        "self_pos",
        f"\tWhere are you currently (out/left/middle/right)?{' [optional]' if mode != 'normal' else ''}: ",
        POSITIONS,
        True
    )


def get_num_doubles() -> Optional[str]:
    return _get_input("number_of_doubles", "\t\tTotal number of doubles inside: ", NUM_DOUBLES)


def get_and_check_calls(init: str,
                        pos: str,
                        limit: Optional[str] = None) -> Optional[dict[str, Optional[str]]]:
    while True:
        try:
            calls = _get_calls(init, pos, limit)
            symbols = list(calls.values())
            if all(isinstance(call, str) for pos, call in calls.items()):
                all_inits_contained = all([init[i] in symbols[i] for i in range(len(init))])
                total_symbols_match = all(''.join(symbols).count(s) == 2 for s in init)
                total_count_match = len(''.join(symbols)) == 6

                if not (all_inits_contained and total_symbols_match and total_count_match):
                    error_message = (f"\t\t\t{'Outside' if pos == 'o' else 'Inside'} inputs invalid.\n"
                                     f"{'\t\t\tAll called symbols have to occur at least once per side.\n' if not all_inits_contained else ''}"
                                     f"{'\t\t\tSymbols can occur at most twice in total.\n' if not total_symbols_match else ''}")
                    raise IOError(error_message)
                else:
                    return calls

            elif limit is not None:
                i_side = 0 if limit == 'left' else 1 if limit == 'middle' else 2
                init_contained = init[i_side] in symbols[i_side]

                if not init_contained:
                    error_message = (f"\t\t\t{'Outside' if pos == 'o' else 'Inside'} inputs invalid.\n"
                                     f"\t\t\tThe called symbol has to occur at least once per side.\n")
                    raise IOError(error_message)
                else:
                    return calls

        except IOError as e:
            if str(e):
                print_colour(e, "red")


def _get_calls(init: str,
               io: str,
               limit: Optional[str] = None) -> dict[str, Optional[str]]:
    if limit is None or limit == "left":
        input_valid = False
        while not input_valid:
            left = _get_input('l', f"\t\t{'Outside statue' if io == 'o' else 'Inside wall'} left (ex. 'cs'): ", BODIES)
            if init[0] in left:
                input_valid = True
            else:
                print_colour(f"\t\t\t{'Outside statue' if io == 'o' else 'Inside wall'} left call must "
                             f"contain {init[0]} at least once.", 'red')
    else:
        left = None

    if limit is None or limit == "middle":
        input_valid = False
        while not input_valid:
            middle = _get_input('m', f"\t\t{'Outside statue' if io == 'o' else 'Inside wall'} middle (ex. 'cs'): ", BODIES)
            if init[1] in middle:
                input_valid = True
            else:
                print_colour(f"\t\t\t{'Outside statue' if io == 'o' else 'Inside wall'} middle call must "
                             f"contain {init[1]} at least once.", 'red')
    else:
        middle = None

    if limit is None or limit == "right":
        if left and middle:
            right = ''.join([s for s in list(SHAPES.keys()) * 2  if ''.join([left, middle]).count(s) < 2][:2])
            print_colour(f"\t\t{'Outside statue' if io == 'o' else 'Inside wall'} right: {right}\n", 'green')
        else:
            input_valid = False
            while not input_valid:
                right = _get_input('r', f"\t\t{'Outside statue' if io == 'o' else 'Inside wall'} right (ex. 'cs'): ", BODIES)
                if init[2] in right:
                    input_valid = True
                else:
                    print_colour(f"\t\t\t{'Outside statue' if io == 'o' else 'Inside wall'} right call must "
                                 f"contain {init[2]} at least once.", 'red')
    else:
        right = None

    return {"left": left, "middle": middle, "right": right}


def _get_input(input_type: str,
               prompt: str,
               ref: dict[str, list[str]],
               is_optional: bool = False) -> Optional[str]:
    user_input = input(f"\033[{COLOURS['green']}m{prompt}\033[0m").lower()

    if user_input == "exit":
        sys.exit()
    if user_input == "restart":
        raise RuntimeError
    if is_optional and user_input == "":
        return None

    info_message, error_msg = _create_msgs(input_type, ref, "Inside" in prompt)
    if user_input in ["h", "help"]:
        print_colour(info_message)
        input_type = "help"

    for k, v in ref.items():
        if user_input in v:
            user_input = k
            break

    if _create_criteria(user_input, input_type, ref):
        return user_input
    else:
        if input_type not in ["help", "back", "rback"]:
            raise IOError(error_msg)
        else:
            raise IOError()


def _create_msgs(input_type: str,
                 ref: dict[str, list[str]],
                 is_wall=False) -> tuple[str, str]:
    skip = '' if input_type in SKIP_EXCEPTED_TYPES else '\t'
    if input_type == "init":
        info_message = (f"\t\tWhat are the statues inside holding (left-to-right)?\n"
                        f"\t\tShape inits consist of unique 3-digit combinations of 'c', 's', and 't':\n"
                        f"\t\t\tall existing inits: cst, cts, sct, stc, tcs, tsc\n")
    elif input_type == "number_of_doubles":
        info_message = f"\t\tNumber of doubles across all inside rooms (either 0, 1, or 3)\n"
    else:
        if input_type == "self_pos":
            input_type = "position"
        elif input_type in ["l", "m", "r"]:
            input_type = "bodie" if not is_wall else "wall call"
        info_message = (f"\t{skip}Known {input_type}s include:\n"
                        f"\t\t{skip}{f'\n\t\t{skip}'.join([f'{k} (accepted inputs: {v})' for k, v in ref.items()])}\n")

    if input_type == "bodie":
        input_type = "body"
    return info_message, f"\t{skip}Invalid {input_type} given.\n" + info_message


def _create_criteria(input_val: str,
                     input_type: str,
                     ref: dict[str, list[str]]) -> bool:
    if input_type == "init":
        criteria = (len(input_val) == 3) and (not any((input_val.count(s) > 1) or (s not in ref.keys()) for s in input_val))
    # TODO: Fill in for new input type, if need be
    elif input_type == "help":
        criteria = False
    else:
        criteria = input_val in ref.keys()
    return criteria
