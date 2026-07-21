from typing import Optional


def calc_n_assembly(init: str,
                    calls: dict[str, str],
                    n_strat: Optional[str],
                    num_doubles: Optional[int] = None) -> dict[str, list[tuple[str]]]:
    if n_strat == "speed":
        steps = _n_speed_strat(init, calls, num_doubles)
    else:
        steps = _n_double_up_strat(init, calls)
    return steps


def calc_c_assembly(calls: dict[str, str],
                    returns: str) -> list[tuple[str]]:
    steps = []
    swap_steps = []
    for i, (start_pos, symbols) in enumerate(calls.items()):
        t_symbol = returns[i]
        if symbols.count(t_symbol) == 0:
            for s in symbols:
                t_side = list(calls.keys())[returns.index(s)]
                steps.append((start_pos, s, t_side))
        else:
            remaining_s = symbols
            for s in remaining_s:
                if s != t_symbol:
                    t_side = list(calls.keys())[returns.index(s)]
                    steps.append((start_pos, s, t_side))
                    remaining_s = remaining_s.replace(s, '', 1)
                else:
                    continue
            steps.append((start_pos, remaining_s, t_side))
            swap_steps.append((start_pos, remaining_s, t_side))

    for start_pos, symbol, t_pos in swap_steps:
        steps.append((t_pos, symbol, start_pos))

    return steps


def _n_speed_strat(init: str,
                   calls: dict[str, str], num_doubles: Optional[int] = None) -> list[tuple[str]]:
    steps = []
    num_doubles = len([None for c in calls.values() if c[0] == c[1]]) if num_doubles is None else num_doubles
    for i, (start_pos, symbols) in enumerate(calls.items()):
        if symbols is not None:
            remaining_init = init[:i] + init[i + 1:]
            remaining_pos = list(calls.keys())
            remaining_pos.pop(i)
            if num_doubles == 0:
                for j in range(2):
                    if symbols is None:
                        continue
                    if remaining_init[j] not in symbols:
                        steps.append((start_pos, symbols[0], remaining_pos[j]))
                        steps.append((start_pos, symbols[1], remaining_pos[j]))
                        break

            elif num_doubles == 1:
                if symbols[0] == symbols[1]:
                    steps.append((start_pos, symbols[0], remaining_pos[0]))
                    steps.append((start_pos, symbols[1], remaining_pos[1]))
                else:
                    if any(symbols[i] == remaining_init[i] for i in range(len(symbols))):
                        symbols = list(reversed(symbols))
                    for j in range(2):
                        steps.append((start_pos, symbols[j], remaining_pos[j]))
            else:
                steps.append((start_pos, symbols[0], remaining_pos[0]))
                steps.append((start_pos, symbols[1], remaining_pos[1]))

    return steps


def _n_double_up_strat(init: str,
                       calls: dict[str, str]) -> list[tuple[str]]:
    steps = []
    all_doubled = all([c[0] == c[1] if c is not None else True for c in calls.values()])
    for i, (start_pos, symbols) in enumerate(calls.items()):
        if symbols is not None:
            remaining_init = init[:i] + init[i + 1:]
            remaining_pos = list(calls.keys())
            remaining_pos.pop(i)

            if not all_doubled:
                for s in symbols:
                    if s != init[i]:
                        steps.append((start_pos, s, remaining_pos[remaining_init.index(s)]))
                steps.append((start_pos, 'wait', start_pos))
            steps.append((start_pos, init[i], remaining_pos[0]))
            steps.append((start_pos, init[i], remaining_pos[1]))

    return steps
