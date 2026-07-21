# Verity This!

The all-in-one guide to Destiny 2's *Salvation's Edge* 4th encounter, **Verity**.

`Verity This!` is a command-line companion tool that walks a fireteam through the Verity encounter step by step. It supports both the **speed** and **double_up** strategies, and gives call-outs, plate/dunk instructions, and challenge/triumph guidance based on your team's live inputs each round.

> **Note:** This tool is by no means perfect and may contain bugs. If you run into one, feel free to open an [Issue](https://github.com/Nightknight3000/Verity-This/issues) on GitHub.

## Features

- Guided, round-by-round instructions for all 3 rounds of the Verity encounter
- Support for both `speed` and `double_up` strategies
- Handles inside/outside positioning and symbol calls
- Triumph and challenge-mode guidance
- Simple colour-coded console interface
- Built-in `help`, `restart`, and `exit` commands available at any time

## Requirements

**None** — if you run the tool via the provided Windows executable (`bin/windows`), there is nothing else to install.

If you'd rather run it from source, you'll need:

- Python 3.9+

## Getting Started

### Option 1: Run the executable (Windows)

1. Download the repository or the latest [release](https://github.com/Nightknight3000/Verity-This/releases).
2. Run the executable found in `bin/windows`.
3. Follow the on-screen prompts.

### Option 2: Run from source

```bash
git clone https://github.com/Nightknight3000/Verity-This.git
cd Verity-This
python verity_this.py
```

## Usage

On launch, you'll be asked to select a mode and, where relevant, a strategy (`speed` or `double_up`). For each of the 3 rounds, the tool will prompt you for:

- The current initiation/symbol setup
- Your position (outside/inside-left/middle/right)
- The team's symbol calls (or only yours in normal mode)
- The number of doubled symbols (only during speed strat in normal mode)

Based on your answers, `Verity This!` will output the exact instructions for that round.

At any point during the prompts, you can type:

| Command | Action |
|---|---|
| `h` / `help` | Show instructions |
| `restart` | Restart the application |
| `exit` | Quit the application |

## Project Structure

```
Verity-This/
├── bin/windows/     # Standalone Windows executable
├── src/
│   ├── algorithm/   # Core instruction-generation logic
│   ├── io/          # Input handling and validation
│   └── utils/       # Constants and shared helpers (e.g. coloured console output)
├── verity_this.py   # Entry point
└── LICENSE
```

## Author

- **Nightknight3000** (Bungie Name: `HawkS0UL#2153`)

## License

This project is licensed under the [Apache-2.0 License](LICENSE).

## Support

If this tool helped you clear Verity, consider leaving a ⭐ on the repo and sharing it with your fireteam!