import os
os.system("cls")
from typing import Optional, Any

from src.algorithm.instructions import give_instructions
from src.io.read_inputs import get_mode, get_normal_strat, get_init, get_self_pos, get_and_check_calls, get_num_doubles
from src.utils.utils import print_colour, COLOURS


def main() -> bool:
    skip_str = "======================================================================================================="
    header = "Verity This!"
    help_msg = "use 'h' or 'help' anytime for instructions,"
    restart_msg = "'restart' to restart the application,"
    exit_msg = "or 'exit' to end the application"
    fill_header_spaces = ' '.join(['' for _ in range(int((len(skip_str) - len(header)) / 2))])
    header_underline = '*'.join(['' for _ in range(len(header) + 1)])
    fill_help_spaces = ' '.join(['' for _ in range(len(skip_str) - len(help_msg))])
    fill_restart_spaces = ' '.join(['' for _ in range(len(skip_str) - len(restart_msg))])
    fill_exit_spaces = ' '.join(['' for _ in range(len(skip_str) - len(exit_msg))])
    print_colour(skip_str)
    print_colour(f"{fill_header_spaces}{header_underline}{fill_header_spaces}", 'yellow')
    print_colour(f"{fill_header_spaces}{header}{fill_header_spaces}", 'yellow')
    print_colour(f"{fill_header_spaces}{header_underline}{fill_header_spaces}", 'yellow')
    print_colour(f"{fill_help_spaces}{help_msg}")
    print_colour(f"{fill_restart_spaces}{restart_msg}")
    print_colour(f"{fill_exit_spaces}{exit_msg}")
    print_colour(skip_str)

    mode = _await_input("mode")
    n_strat = _await_input("n_strat") if mode in ["normal", "all_normal"] else "speed"
    last_dunk = None

    for i in range(1, 4):
        print_colour(skip_str)
        print_colour(f"Round {i}", 'yellow')

        user_inputs = []
        while len(user_inputs) < 4:
            init = _await_input("init")
            user_inputs.append(init)
            self_pos = _await_input("self_pos", mode)
            user_inputs.append(self_pos)
            if isinstance(mode, str) and isinstance(init, str):
                calls, num_doubles = _get_calls(mode, n_strat, init, self_pos)
                user_inputs.append(calls)
                user_inputs.append(num_doubles)
            else:
                raise TypeError(f"Unexpected type for {[x for x in [mode, init] if not isinstance(x, str)]} "
                                f"(should be 'str'): {','.join([f'type({x})={str(type(x))}' for x in [mode, init] if not isinstance(x, str)])}")

        last_dunk = give_instructions(mode, n_strat, init, self_pos, calls, num_doubles, i, last_dunk)

    print_colour(skip_str)
    print_colour(f"Thank you for using Verity This!\n"
                 f"Feel free to leave a *star* and share the GitHub repo (https://github.com/Nightknight3000/Verity-This).",
                 'yellow')
    return input(f"\033[{COLOURS['green']}mRestart (y/N)?:\033[0m").lower() == 'y'


def _await_input(input_type: str, mode: Optional[str] = None) -> Optional[str]:
    input_valid = False
    user_input = None
    while not input_valid:
        try:
            if input_type == "mode":
                user_input = get_mode()
            elif input_type == "n_strat":
                user_input = get_normal_strat()
            elif input_type == "init":
                user_input = get_init()
            elif input_type == "self_pos":
                user_input = get_self_pos(mode)
            else:
                user_input = 'undefined'
            if (input_type == "self_pos") and (mode == "normal") and (user_input is None):
                print_colour("\t\tIn normal mode, a position has to be specified.", "red")
                continue
            input_valid = True
        except IOError as e:
            if str(e):
                print_colour(e, "red")
    return user_input


def _get_calls(mode: str,
               n_strat: Optional[str],
               init: str,
               self_pos: Optional[str]) -> tuple[dict[str, Any], Optional[int]]:
    num_doubles = None
    if mode == "normal":
        if self_pos == "outside":
            calls = get_and_check_calls(init, 'o')
        else:
            calls = get_and_check_calls(init, 'i', self_pos)
            while True:
                try:
                    num_doubles = int(get_num_doubles()) if n_strat == "speed" else None
                    if num_doubles is not None:
                        if any([c[0] == c[1] for c in list(calls.values()) if c is not None]) and int(num_doubles) == 0:
                            error_message = (
                                f"\t\t\tThe given call is doubled, but num_doubles = {num_doubles} was given "
                                f"which is not possible then.")
                            raise IOError(error_message)
                        elif any([c[0] != c[1] for c in list(calls.values()) if c is not None]) and int(
                                num_doubles) == 3:
                            error_message = (
                                f"\t\t\tThe given call is not doubled, but num_doubles = {num_doubles} was given "
                                f"which is not possible then.")
                            raise IOError(error_message)
                    break
                except IOError as e:
                    if str(e):
                        print_colour(e, "red")
    else:
        calls = {}
        for pos in "io":
            calls[pos] = get_and_check_calls(init, pos)
    return calls, num_doubles


if __name__ == "__main__":
    run = True
    while run:
        try:
            run = main()
        except RuntimeError as e:
            run = True
            os.system("cls")
        except SystemExit:
            run = False
