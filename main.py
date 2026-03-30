"""
E-commerce Big Data analytics — CLI entrypoint.

The full workflow lives in ``pipeline.runner.run_full_pipeline``. Configuration
(paths, quick mode, dataset sizes) lives in ``config.py``.
"""

from __future__ import annotations

from pipeline.runner import run_full_pipeline
from project_summary import FINAL_SUMMARY_TEXT

# Re-export for Streamlit and notebooks: ``from main import FINAL_SUMMARY_TEXT``
__all__ = ["main", "FINAL_SUMMARY_TEXT", "run_full_pipeline"]


def main() -> None:
    run_full_pipeline()


if __name__ == "__main__":
    main()
