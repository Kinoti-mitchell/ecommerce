"""Batch pipeline orchestration (analytics steps wired after the data lake)."""

from .runner import run_full_pipeline

__all__ = ["run_full_pipeline"]
