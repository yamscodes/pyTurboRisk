"""
pyTurboRisk - Python Port

This is the Python port of the TurboRisk strategy game, originally written
in Lazarus/Free Pascal.

The port includes:
- Core game engine
- TRSim (simulation tool)
- TRSimCLI (command-line simulation runner)
- TRComp (TRP compiler/editor)
- TRMap (map editor)
- TRP scripting engine (PascalScript)

To run:
    python -m trsim.trsim_cli --schedule games.csv --map std_map_small.trm

For development:
    pip install -r requirements.txt
"""

__version__ = '0.1.0'
