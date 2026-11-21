"""Run a solution against every test case in a problem folder.

Usage:
    python tools/run.py <problem_dir> [--cmd "command to run"] [--timeout SECONDS]

The solution reads stdin and writes stdout, like the real judge. By default
the single *.py file in <problem_dir> is run with the current Python. Use
--cmd for anything else (e.g. --cmd "./a.out").

Every *.in under sample/ and secret/ is run and compared with its .ans file
(tokens compared, so whitespace differences don't matter).
"""
import argparse
import shlex
import subprocess
import sys
import time
from pathlib import Path


def find_command(problem: Path) -> list[str]:
    sols = [p for p in problem.glob("*.py") if not p.name.startswith(".")]
    if len(sols) != 1:
        sys.exit(f"Expected exactly one .py file in {problem}, found {len(sols)}. Use --cmd.")
    return [sys.executable, str(sols[0])]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("problem", type=Path)
    ap.add_argument("--cmd", help="command to run instead of the .py file")
    ap.add_argument("--timeout", type=float, default=60.0)
    args = ap.parse_args()

    problem = args.problem.resolve()
    cmd = shlex.split(args.cmd) if args.cmd else find_command(problem)
    cases = sorted(
        p for d in ("sample", "secret") for p in (problem / d).rglob("*.in")
    )
    if not cases:
        sys.exit(f"No .in files under {problem}/sample or {problem}/secret")

    failed = 0
    for inp in cases:
        ans = inp.with_suffix(".ans")
        label = inp.relative_to(problem).as_posix()
        start = time.perf_counter()
        try:
            with inp.open("rb") as f:
                res = subprocess.run(cmd, stdin=f, capture_output=True, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            print(f"TLE   {label}  (> {args.timeout:.0f}s)")
            failed += 1
            continue
        elapsed = time.perf_counter() - start

        if res.returncode != 0:
            status = "RE  "
            detail = res.stderr.decode(errors="replace").strip().splitlines()[-1:] or [""]
        elif not ans.exists():
            status, detail = "??  ", ["no .ans file"]
        else:
            got, want = res.stdout.split(), ans.read_bytes().split()
            if got == want:
                status, detail = "OK  ", []
            else:
                status = "WA  "
                lines_got = res.stdout.decode(errors="replace").splitlines()
                lines_want = ans.read_text(errors="replace").splitlines()
                diff = next(
                    (i for i, (a, b) in enumerate(zip(lines_got, lines_want)) if a.split() != b.split()),
                    min(len(lines_got), len(lines_want)),
                )
                g = lines_got[diff] if diff < len(lines_got) else "<missing>"
                w = lines_want[diff] if diff < len(lines_want) else "<extra output>"
                detail = [f"line {diff + 1}: got {g!r}, want {w!r}"]
        if status != "OK  ":
            failed += 1
        print(f"{status}  {label}  {elapsed:6.2f}s  {' '.join(detail)}")

    print(f"\n{len(cases) - failed}/{len(cases)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
