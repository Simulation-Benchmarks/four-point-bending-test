"""Run the ANSYS four-point-bending Snakemake workflow (ansys_models) from Python.

Usage (from an environment with snakemake, see ../environment_snakemake.yml):

    python run_benchmark.py                       # drucker_prager
    python run_benchmark.py --model microplane
    python run_benchmark.py --model both          # run both models
"""

import argparse
import subprocess
import sys
from pathlib import Path

WORKDIR = Path(__file__).resolve().parent
MODELS = ("drucker_prager", "microplane")


def run_snakemake_workflow(model: str, cores: int, extra_args: list[str]) -> None:
    cmd = [
        sys.executable, "-m", "snakemake",
        "--snakefile", str(WORKDIR / "Snakefile"),
        "--directory", str(WORKDIR),
        "--force",
        "--cores", str(cores),
        "--config", f"model={model}",
        *extra_args,
    ]
    print(f"Running [{model}]: {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", choices=(*MODELS, "both"), default="drucker_prager")
    parser.add_argument("--cores", type=int, default=1)
    args, extra = parser.parse_known_args()  # unknown args are passed on to snakemake

    for model in MODELS if args.model == "both" else (args.model,):
        run_snakemake_workflow(model, args.cores, extra)


if __name__ == "__main__":
    main()
