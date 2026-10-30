"""Run the Eurocode 2 Snakemake workflow (eurocode_model) from Python.

Usage (from an environment with snakemake, see ../environment_snakemake.yml):

    python run_benchmark.py
    python run_benchmark.py --cores 2
"""

import argparse
import subprocess
import sys
from pathlib import Path

WORKDIR = Path(__file__).resolve().parent


def run_snakemake_workflow(cores: int, extra_args: list[str]) -> None:
    cmd = [
        sys.executable, "-m", "snakemake",
        "--snakefile", str(WORKDIR / "Snakefile"),  # the Snakefile sets workdir to the repo root
        "--force",
        "--cores", str(cores),
        *extra_args,
    ]
    print(f"Running: {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cores", type=int, default=1)
    args, extra = parser.parse_known_args()  # unknown args are passed on to snakemake

    run_snakemake_workflow(args.cores, extra)


if __name__ == "__main__":
    main()
