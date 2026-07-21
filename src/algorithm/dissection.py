from typing import Optional, Union

from src.utils.constants import POSITIONS


def calc_n_dissection(init: str,
                      calls: dict[str, str]) -> list[tuple[str]]:
    goals = _set_goals(init)
    return _calc_dissection(init, calls, goals)


def calc_c_dissection(init: str,
                      calls: dict[str, str],
                      is_challenge_round: bool = False) -> tuple[list[tuple[str]], str]:
    goals = _set_goals(init, is_challenge_round)
    return _calc_dissection(init, calls, goals)


def _calc_dissection(init: str,
                     calls: dict[str, str],
                     goals: dict[str, str]) -> Union[list[tuple[str]], tuple[list[tuple[str]], str]]:
    steps = []
    if sorted(list(goals.values())) == sorted(["cs", "ct", "st"]):
        num_doubles = len([c for c in calls.values() if c[0] == c[1]])
        positions = list(calls.keys())
        if num_doubles == 0:
            for i in range(3):
                steps.append((init[i], positions[i]))
            if init[0] in calls[positions[1]]:
                steps.append((init[0], positions[1]))
            else:
                steps.append((init[1], positions[0]))
        elif num_doubles == 1:
            double_pos = -1
            for i in range(3):
                if calls[positions[i]][0] == calls[positions[i]][1]:
                    double_pos = i
                    break
            steps.append((init[double_pos], positions[double_pos]))
            for i in range(3):
                if double_pos != 0:
                    steps.append((init[i], positions[i]))
                else:
                    i_pos = i + 1 if i + 1 < 3 else 0
                    steps.append((init[i_pos], positions[i_pos]))
        else:
            for i in range(3):
                steps.append((init[i], positions[i]))
            for i in range(3):
                steps.append((init[i], positions[i]))
        return steps

    else:
        is_double = [c[0] == c[1] for c in calls.values()]
        positions = list(calls.keys())
        if sum(is_double) == 0:
            for i in range(3):
                steps.append((init[i], positions[i]))
            new_call_left = calls[positions[0]].replace(init[0], init[1], 1)
            new_call_middle = calls[positions[1]].replace(init[1], init[0], 1)
            new_non_double = positions[1] if new_call_left[0] == new_call_left[1] else positions[0]
            replace_s = new_call_left.replace(init[2], '', 1) if new_non_double == 'left' else new_call_middle.replace(init[2], '', 1)
            steps.append((replace_s, new_non_double))

            returns = _calc_returns(calls, steps)
        elif sum(is_double) == 1:
            d_pos, d_symbol = [(pos, symbols[0]) for pos, symbols in calls.items() if symbols[0] == symbols[1]][0]
            remain_pos = [pos for pos in calls.keys() if pos != d_pos]
            remain_symbols = [s for s in init if s != d_symbol]
            for s in remain_symbols:
                steps.append((s, remain_pos[0]))
                steps.append((d_symbol, d_pos))
            fin_s = init[positions.index(remain_pos[1])]
            steps.append((fin_s, remain_pos[1]))
            remain_symbols.remove(fin_s)
            steps.append((remain_symbols[0], d_pos))

            returns = _calc_returns(calls, steps)
        else:
            for i in range(3):
                steps.append((init[i], positions[i]))
            for i in range(2):
                steps.append((init[i], positions[i]))
            steps.append((init[2], positions[0]))
            steps.append((init[0], positions[1]))
            steps.append((init[2], positions[2]))

            returns = _calc_returns(calls, steps)
        return steps, returns


def _set_goals(init: str,
               is_challenge_round: bool = False) -> dict[str, str]:
    if not is_challenge_round:
        return {list(POSITIONS.keys())[i+1]: ''.join(sorted(init[:i] + init[i+1:])) for i in range(3)}
    else:
        return {list(POSITIONS.keys())[i+1]: init[i+1 if i+1 < 3 else 0] * 2 for i in range(3)}


def _calc_returns(calls: dict[str, str],
                  steps: list[tuple[str]]) -> str:
    buffer = None
    for symbol, pos in steps:
        if buffer is None:
            buffer = (symbol, pos)
        else:
            b_symbol, b_pos = buffer
            calls[b_pos] = calls[b_pos].replace(b_symbol, symbol, 1)
            calls[pos] = calls[pos].replace(symbol, b_symbol, 1)
            buffer = None
    returns = ''
    for _, symbols in calls.items():
        returns += symbols[0]
    return returns
