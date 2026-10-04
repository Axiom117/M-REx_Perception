"""Headless command line interface.

Usage::

    python -m mrex_perception.cli run --config default --source random \
        --count 6 --seed 42 --steps 50 --report out.json

Runs the simulation engine without importing Qt/VTK, prints the
``simulationSummary.m``-style report for manual comparison and optionally
writes the numeric summary as JSON for machine comparison.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.engine import EngineParams, FinishReason, SimulationEngine
from mrex_perception.core.reporting import SummaryReport
from mrex_perception.core.setup import populate_random


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m mrex_perception.cli",
        description="M-REx Perception headless tools",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="run a simulation and print its summary")
    run.add_argument(
        "--config", default="default", help="workspace config name (default: %(default)s)"
    )
    run.add_argument(
        "--source",
        choices=("random",),
        default="random",
        help="embryo source (image arrives in M5; default: %(default)s)",
    )
    run.add_argument(
        "--count", type=int, default=6, help="number of random embryos (default: %(default)s)"
    )
    run.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible runs")
    run.add_argument(
        "--steps", type=int, default=50, help="interpolation steps per move (default: %(default)s)"
    )
    run.add_argument(
        "--target",
        type=float,
        nargs=3,
        default=(50.0, 50.0, 0.1),
        metavar=("X", "Y", "Z"),
        help="selection target point (default: 50 50 0.1)",
    )
    run.add_argument(
        "--report", type=Path, default=None, help="write the summary as JSON to this path"
    )
    return parser


def _vec3(values: np.ndarray, decimals: int) -> str:
    return "[" + ", ".join(f"{value:.{decimals}f}" for value in values) + "]"


def format_summary_text(report: SummaryReport) -> str:
    """fprintf-style text matching ``simulationSummary.m`` (for manual diffing)."""
    lines = [
        "----- Simulation Summary -----",
        f"Total embryos:        {report.total}",
        f"Successfully moved:   {report.moved}",
        f"Failed embryos:       {report.failed}",
        f"Free remaining:       {report.free}",
        f"Still selected:       {report.selected}",
        f"Still grasped:        {report.grasped}",
        f"Total grasp attempts: {report.total_attempts}",
        f"Successful pickups:   {report.successful_pickups}",
        f"Average attempts:     {report.average_attempts:.2f}",
        f"Success rate:         {report.success_rate:.1f}%",
        "------------------------------",
        "",
        "----- Tool Motion Summary -----",
        f"Recorded motion samples: {report.num_motion_samples}",
        "",
        "Position information:",
        f"Start position:          {_vec3(report.start_position, 3)} mm",
        f"Final position:          {_vec3(report.final_position, 3)} mm",
        f"Minimum position:        {_vec3(report.minimum_position, 3)} mm",
        f"Maximum position:        {_vec3(report.maximum_position, 3)} mm",
        f"XYZ position range:      {_vec3(report.position_range, 3)} mm",
        "",
        "Distance information:",
        f"Total tool distance:     {report.total_tool_distance:.3f} mm",
        f"Minimum movement step:   {report.minimum_segment_distance:.3f} mm",
        f"Maximum movement step:   {report.maximum_segment_distance:.3f} mm",
        f"Average movement step:   {report.average_segment_distance:.3f} mm",
        "",
        "Rotation information (roll, pitch, yaw):",
        f"Minimum orientation:     {_vec3(report.minimum_rotation_deg, 2)} deg",
        f"Maximum orientation:     {_vec3(report.maximum_rotation_deg, 2)} deg",
        f"Maximum yaw adjustment:  {report.maximum_yaw_adjustment_deg:.2f} deg",
        f"Average yaw adjustment:  {report.average_yaw_adjustment_deg:.2f} deg",
        f"Orientation range:       {_vec3(report.rotation_range_deg, 2)} deg",
        f"Net rotation:            {_vec3(report.net_rotation_deg, 2)} deg",
        f"Cumulative rotation:     {_vec3(report.cumulative_rotation_deg, 2)} deg",
        f"Total angular motion:    {report.total_angular_motion_deg:.2f} deg",
        "--------------------------------",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    try:
        workspace = load_workspace(args.config)
        rng = np.random.default_rng(args.seed)
        embryos = populate_random(args.count, workspace, rng)
        engine = SimulationEngine(
            workspace,
            embryos,
            EngineParams(num_steps=args.steps, target_point=np.asarray(args.target, dtype=float)),
            rng=rng,
        )
        result = engine.run()

        if result.finish_reason == FinishReason.STOPPED:
            print("Simulation stopped before completion.")
            return 1

        summary = result.summary
        if summary is None:
            print("[error] completed run without a summary", file=sys.stderr)
            return 1

        print(format_summary_text(summary))

        if args.report is not None:
            payload = {"finish_reason": str(result.finish_reason), "summary": summary.to_dict()}
            args.report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(f"[report] wrote {args.report}")
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
