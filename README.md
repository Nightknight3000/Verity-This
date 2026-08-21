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
- Optional point-and-click **GUI version** (`bin/windows/verity_this_gui.exe`) with switchable themes, English/German language support, and Undo — see [GUI Version](#gui-version) below

## Requirements

**None** — if you run the tool via one of the provided Windows executables (`bin/windows`), there is nothing else to install.

If you'd rather run it from source, you'll need:

- Python 3.9+
- Tkinter (only for the GUI version — included with most standard Python installs)

## Getting Started

### Option 1: Run the executable (Windows)

1. Download the repository or the latest [release](https://github.com/Nightknight3000/Verity-This/releases).
2. Navigate into the `bin/windows` folder:
   ```bash
   cd bin\windows
   ```
3. Run one of the two executables found there:
   | Executable | Starts |
   |---|---|
   | `verity_this.exe` | The console interface |
   | `verity_this_gui.exe` | The point-and-click [GUI version](#gui-version) |

   Double-click it in Explorer, or launch it from a terminal already inside `bin\windows`:
   ```bash
   .\verity_this_gui.exe
   ```
4. Follow the on-screen prompts.

### Option 2: Run from source

```bash
git clone https://github.com/Nightknight3000/Verity-This.git
cd Verity-This
python verity_this.py
```

To run the GUI version from source instead:

```bash
python gui_native.py
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

## GUI Version

`verity_this_gui.exe` (or `python gui_native.py` from source) gives you the exact same guided flow as the console version, but as a point-and-click window instead of typed commands:

- **New Session** / **Undo** / **Exit tool** buttons, plus an **Always on top** toggle
- Every question is answered by clicking a button instead of typing — invalid or out-of-order options are greyed out automatically
- A **Theme** dropdown (`Default`, `Solarized Dark`, `Warm Paper`, `Neon Cyberpunk`)
- A **Language** dropdown (`English`, `Deutsch`)

Whichever Theme and Language you last selected becomes the default the next time you open the GUI — no need to reselect them every session.

## Project Structure

```
Verity-This/
├── bin/windows/       # Standalone Windows executables
│   ├── verity_this.exe       # Console interface
│   └── verity_this_gui.exe   # Point-and-click GUI
├── src/
│   ├── algorithm/     # Core instruction-generation logic
│   ├── io/            # Input handling and validation
│   └── utils/         # Constants and shared helpers (e.g. coloured console output, GUI text/labels)
├── verity_this.py     # Console entry point
├── gui_native.py      # GUI entry point
└── LICENSE
```

## Author

- **Nightknight3000** (Bungie Name: `HawkS0UL#2153`)

## License

This project is licensed under the [Apache-2.0 License](LICENSE).

## Support

If this tool helped you clear Verity, consider leaving a ⭐ on the repo and sharing it with your fireteam!