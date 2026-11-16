# pyTurboRisk - Python Port

This is a Python port of the TurboRisk strategy game, originally written in Lazarus/Free Pascal.

## Overview

TurboRisk is a Risk-style strategy game that supports:
- Human vs AI gameplay
- Multiple AI opponents with different strategies
- Custom maps
- TRP (TurboRisk Program) scripting for custom AI
- Simulation and testing tools

This Python port aims to provide the same functionality as the original Pascal version, with a focus on:
- Maintaining compatibility with existing TRP scripts
- Providing a command-line interface for simulations
- Supporting the same game rules and mechanics

## Project Structure

```
python_port/
├── turborisk/           # Core game engine
│   ├── __init__.py
│   ├── globals.py      # Global state and constants
│   ├── territory.py    # Territory and map handling
│   ├── exp_subr.py     # External functions for TRP scripts
│   └── computer.py     # Computer player logic
├── trsim/              # Simulation tools
│   ├── __init__.py
│   └── trsim_cli.py    # Command-line simulation runner
├── trcomp/             # TRP compiler (TBD)
├── trmap/              # Map editor (TBD)
├── tests/              # Test suite
│   └── test_basic.py
├── players/            # TRP bot scripts (TBD)
├── maps/               # Map files (TBD)
├── requirements.txt
└── README.md
```

## Installation

```bash
# Clone the repository
cd python_port

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running a Simulation

```bash
# Basic simulation with a schedule file
python -m trsim.trsim_cli --schedule games.csv --map std_map_small.trm

# With verbose output
python -m trsim.trsim_cli --schedule games.csv --map std_map_small.trm --verbose

# With turn limit
python -m trsim.trsim_cli --schedule games.csv --map std_map_small.trm --turn-limit 20

# With a specific random seed for reproducibility
python -m trsim.trsim_cli --schedule games.csv --map std_map_small.trm --seed 42
```

### Schedule File Format

The schedule file contains one game roster per line, with comma-separated player names:

```csv
# Comment line
simple.trp,rambo.trp,napoleon.trp
borg.trp,alexander.trp,digger.trp
# Another game
turtle.trp,doomstack.trp,actuary.trp
```

Player names may include or omit the `.trp` extension.

### Command-line Options

| Option | Description |
|--------|-------------|
| `--schedule <file>` | Required. Schedule file with game rosters |
| `--map <file.trm>` | Map file (default: std_map_small.trm) |
| `--game-log <file>` | Game log file (default: TRSimCLI.sgl) |
| `--cpu-log <file>` | CPU usage log file (default: TRSimCLI.scl) |
| `--action-log <file>` | Optional action history (JSONL format) |
| `--turn-limit <n>` | Maximum turns per game (0: unlimited) |
| `--time-limit <s>` | Maximum seconds per game (0: unlimited) |
| `--seed <n>` | Random number generator seed |
| `--verbose` | Log TRP decisions and action outcomes |
| `--error-dump` | Write game dump when a TRP errors |
| `--statistically-significant-sample` | Run until statistical significance |
| `--allow-duplicate-players` | Allow same bot multiple times in a game |

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run a specific test file
python -m pytest tests/test_basic.py -v
```

### Porting TRP Scripts

TRP (TurboRisk Program) scripts are written in a Pascal-like language. The Python port provides a compatible API through the `exp_subr` module.

Example TRP functions available:
- `TName(T)` - Get territory name
- `TOwner(T)` - Get territory owner
- `TArmies(T)` - Get army count on territory
- `TIsMine(T)` - Check if territory is owned by current player
- `PMe()` - Get current player ID
- `PArmiesCount(P)` - Get total armies for player
- `URandom(R)` - Get random number between 0 and R-1
- `UMessage(M)` - Display a message
- `ULog(M)` - Log a message

See `turborisk/exp_subr.py` for the complete list of available functions.

## Current Status

### Completed
- [x] Core data types and constants (Globals.pas)
- [x] Territory and map handling (Territ.pas)
- [x] External TRP API functions (ExpSubr.pas)
- [x] Computer player logic (Computer.pas)
- [x] TRSimCLI command-line interface
- [x] Basic test suite

### In Progress
- [ ] TRP scripting engine (PascalScript)
- [ ] TRComp compiler/editor
- [ ] TRMap map editor
- [ ] Main TurboRisk game GUI
- [ ] Porting TRP bot scripts to Python

### Not Started
- [ ] Advanced GUI features
- [ ] Network multiplayer
- [ ] Full TRP language support

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the same terms as the original TurboRisk game.
See the LICENSE.md file in the parent directory for details.

## Original Project

The original TurboRisk game was written by Mario Ferrari and ported to Lazarus/Free Pascal.
This Python port maintains compatibility with the original game's features and TRP scripts.

## Contact

For questions or issues, please open a GitHub issue or contact the project maintainers.
