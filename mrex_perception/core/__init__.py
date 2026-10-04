"""Pure-logic core layer, organized by role (must not import Qt or VTK).

Subpackage layout; dependencies point downward only:

- ``math``      pure helpers: transforms (rotation_z / make_pose), geometry
- ``models``    data models: state enums (states) + entity dataclasses (entities)
- ``setup``     construction: random/detection embryos, clustering, tool head
- ``sim``       runtime behavior: planner, motion (+ motion log), grasping
- ``reporting`` result output: summary statistics

Each subpackage re-exports its public API from ``__init__``, so consumers can
import e.g. ``from mrex_perception.core.models import Embryo``.
"""
