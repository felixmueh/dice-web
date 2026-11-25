"""The dice language: exact tabletop probability calculations.

This package root is the public Python surface. Embedding code and Python
helper modules imported from dice programs write ``from dice import ...``:

- ``dice_interpreter`` / ``DiceSession``: a stateful session that evaluates
  dice source and accepts ``register_function``.
- ``interpret_statement`` / ``interpret_file``: one-shot evaluation.
- ``dicefunction`` and ``D``: mark Python functions as dice callables and
  declare dice-side defaults.
- ``Distribution``, ``FiniteMeasure``, ``Sweep``: the runtime value types that
  typed Python parameters receive.

The implementation lives in the submodules (``dice.lexer`` -> ``dice.diceparser``
-> ``dice.interpreter`` -> ``dice.diceengine``); the CLI is ``python3 -m dice``.
"""

from .cli import DiceSession, dice_interpreter, interpret_file, interpret_statement
from .diceengine import Distribution, FiniteMeasure, Sweep
from .hostfunctions import D, dicefunction

__all__ = [
    "D",
    "DiceSession",
    "Distribution",
    "FiniteMeasure",
    "Sweep",
    "dice_interpreter",
    "dicefunction",
    "interpret_file",
    "interpret_statement",
]
