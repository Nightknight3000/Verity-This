from typing import Optional, Any

from src.algorithm.assembly import calc_n_assembly, calc_c_assembly
from src.algorithm.dissection import calc_n_dissection, calc_c_dissection
from src.utils.utils import print_colour


def give_instructions(mode: str,
                      n_strat: Optional[str],
                      init: str,
                      self_pos: Optional[str],
                      calls: dict[str, Any],
                      num_doubles: Optional[int],
                      round: int,
                      last_dunk: Optional[str] = None) -> Optional[str]:
    if mode == "normal":
        _run_normal(init, calls, num_doubles, n_strat, self_pos)
    elif mode == "all_normal":
        _run_all_normal(init, calls, n_strat, self_pos)
    elif mode == "triumph":
        last_dunk = _run_all_normal(init, calls, n_strat, self_pos, do_triumph=True, last_dunk=last_dunk)
    elif mode == "challenge":
        _run_challenge(init, calls, self_pos, round == 2)
    elif mode == "hard_challenge":
        _run_challenge(init, calls, self_pos, round in [1, 3])
    elif mode == "triumph+challenge":
        last_dunk = _run_challenge(init, calls, self_pos, round == 2, do_triumph=True, last_dunk=last_dunk)
    elif mode == "triumph+hard_challenge":
        last_dunk = _run_challenge(init, calls, self_pos, round in [1, 3], do_triumph=True, last_dunk=last_dunk)
    else:
        pass
    return last_dunk


def _run_normal(init: str,
                calls: Optional[dict[str, Optional[str]]],
                num_doubles: Optional[int],
                n_strat: Optional[str],
                self_pos: Optional[str]) -> None:
    if self_pos == "outside":
        # calls = get_and_check_calls(init, 'o')
        steps = calc_n_dissection(init, calls)
        print_colour("\tOutside steps:", "yellow")
        for symbol, pos in steps:
            print_colour(f"\t\tDunk {symbol} on the {pos} statue", "purple")
    else:
        # calls = get_and_check_calls(init, 'i', self_pos)
        # while True:
        #     try:
        #         num_doubles = int(get_num_doubles()) if n_strat == "speed" else None
        #         if num_doubles is not None:
        #             if any([c[0] == c[1] for c in list(calls.values()) if c is not None]) and int(num_doubles) == 0:
        #                 error_message = (f"\t\t\tThe given call is doubled, but num_doubles = {num_doubles} was given "
        #                                  f"which is not possible then.")
        #                 raise IOError(error_message)
        #             elif any([c[0] != c[1] for c in list(calls.values()) if c is not None]) and int(num_doubles) == 3:
        #                 error_message = (f"\t\t\tThe given call is not doubled, but num_doubles = {num_doubles} was given "
        #                                  f"which is not possible then.")
        #                 raise IOError(error_message)
        #         break
        #     except IOError as e:
        #         if str(e):
        #             print_colour(e, "red")
        steps = calc_n_assembly(init, calls, n_strat, num_doubles)
        print_colour("\tInside steps:", "yellow")
        for pos, symbol, tar in steps:
            if symbol == "wait":
                print_colour(f"\t\tWait until partners are ready...", "purple")
            else:
                print_colour(f"\t\tDunk {symbol} on the {tar} statue", "purple")


def _run_all_normal(init: str,
                    calls: Optional[dict[str, Any]],
                    n_strat: Optional[str],
                    self_pos: Optional[str],
                    do_triumph: bool = False,
                    last_dunk: Optional[str] = None) -> Optional[str]:
    a_steps = calc_n_assembly(init, calls["i"], n_strat)
    d_steps = calc_n_dissection(init, calls["o"])

    print_colour(f"\tInside steps:", "yellow")
    if do_triumph:
        a_steps, last_dunk = _triumph_sort(calls['i'], a_steps, last_dunk)
    i_step = 1
    for pos, sym, tar in a_steps:
        if sym == "wait":
                print_colour(f"\t\tInside {pos}: Wait until partners are ready...",
                             "purple" if pos != self_pos else "lightred")
        else:
            print_colour(f"\t\t{f'{i_step}. ' if do_triumph else ''}"
                         f"Inside {pos}: Dunk {sym} on the {tar} statue",
                         "purple" if pos != self_pos else "lightred")
            i_step += 1
            if do_triumph:
                last_dunk = tar

    print_colour("\n\tOutside steps:", "yellow")
    if do_triumph:
        d_steps, last_dunk = _triumph_sort(calls['o'], d_steps, last_dunk)
    for sym, tar in d_steps:
        print_colour(f"\t\t{f'{i_step}. ' if do_triumph else ''}"
                     f"Outside: Dunk {sym} on the {tar} statue",
                     "purple" if self_pos != "outside" else "lightred")
        i_step += 1

    if do_triumph:
        return last_dunk


def _run_challenge(init: str,
                   calls: Optional[dict[str, Any]],
                   self_pos: Optional[str],
                   is_challenge_round: bool = False,
                   do_triumph: bool = False,
                   last_dunk: Optional[str] = None) -> Optional[str]:
    if is_challenge_round:
        d_steps, returns = calc_c_dissection(init, calls["o"], True)
        a_steps = calc_c_assembly(calls["i"], returns)
    else:
        d_steps = calc_c_dissection(init, calls["o"], False)
        a_steps = calc_n_assembly(init, calls["i"], "speed")

    print_colour(f"\tInside steps:", "yellow")
    if do_triumph:
        a_steps, last_dunk = _triumph_sort(calls['i'], a_steps, last_dunk)
    i_step = 1
    for pos, sym, tar in a_steps:
        if sym == "wait":
            print_colour(f"\t\tInside {pos}: Wait until partners are ready...",
                         "purple" if pos != self_pos else "lightred")
        else:
            print_colour(f"\t\t{f'{i_step}. ' if do_triumph else ''}"
                         f"Inside {pos}: Dunk {sym} on the {tar} statue",
                         "purple" if pos != self_pos else "lightred")
            i_step += 1
            if do_triumph:
                last_dunk = tar

    print_colour("\n\tOutside steps:", "yellow")
    if do_triumph:
        d_steps, last_dunk = _triumph_sort(calls['o'], d_steps, last_dunk)
    for sym, tar in d_steps:
        print_colour(f"\t\t{f'{i_step}. ' if do_triumph else ''}"
                     f"Outside: Dunk {sym} on the {tar} statue",
                     "purple" if self_pos != "outside" else "lightred")
        i_step += 1

    if do_triumph:
        return last_dunk


def _triumph_sort(calls: dict[str, str],
                  steps: list[tuple[str]],
                  last_dunk: Optional[str]) -> tuple[list[tuple[str]], Optional[str]]:
    new_steps, buffer = [], []
    is_inside = len(steps[0]) == 3

    while steps:
        for i, s in enumerate(steps):
            if is_inside:
                if (last_dunk is None) or (((s[0] == last_dunk) or len(steps) <= 2) and (s[1] in calls[s[0]])):
                    new_steps.append(steps.pop(i))
                    calls[s[0]] = calls[s[0]].replace(s[1], '', 1)
                    calls[s[2]] += s[1]
                    last_dunk = s[2]
                    break
            else:
                if s[-1] != last_dunk:
                    new_steps.append(steps.pop(i))
                    last_dunk = s[-1]
                    break

    return new_steps, last_dunk