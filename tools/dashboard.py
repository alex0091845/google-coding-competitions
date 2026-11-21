"""Local practice dashboard: progress, TODOs, and an in-browser editor + test runner.

Usage:
    python tools/dashboard.py [--port 8766] [--no-browser]

Reads learning/*.md and the problem folders, serves tools/dashboard.html on
http://127.0.0.1:<port>. Saving writes the solution .py / NOTES.md in the
problem folder; "Run tests" uses the same logic as tools/run.py.
Standard library only. Binds to localhost only.
"""
import argparse
import difflib
import json
import mimetypes
import re
import subprocess
import sys
import time
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, str(Path(__file__).parent))
import run as runner  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LEARNING = ROOT / "learning"
CONTESTS = ("kickstart", "codejam", "hashcode")
SOLUTION_TEMPLATE = "import sys\n\n\ndef main():\n    pass\n\n\nmain()\n"


# ---------- markdown parsing ----------

def sections(text: str, level: int = 2) -> dict[str, str]:
    """Split markdown into {heading: body} at the given heading level."""
    out, cur, buf = {}, None, []
    mark = "#" * level + " "
    for line in text.splitlines():
        if line.startswith(mark):
            if cur is not None:
                out[cur] = "\n".join(buf).strip()
            cur, buf = line[len(mark):].strip(), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf).strip()
    return out


def parse_table(text: str) -> list[dict]:
    rows = [l.strip() for l in text.splitlines() if l.strip().startswith("|")]
    if len(rows) < 2:
        return []
    split = lambda r: [c.strip() for c in r.strip("|").split("|")]
    head = split(rows[0])
    return [dict(zip(head, split(r))) for r in rows[2:]]


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def similar(a: str, b: str) -> bool:
    a, b = norm(a), norm(b)
    return bool(a and b) and (a == b or difflib.SequenceMatcher(None, a, b).ratio() > 0.85)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


# ---------- repo state ----------

def find_problems() -> list[dict]:
    probs = []
    for c in CONTESTS:
        for st in sorted((ROOT / c).glob("*/*/*/statement.pdf")):
            d = st.parent
            rel = d.relative_to(ROOT).as_posix()
            _, year, rnd, slug = rel.split("/")
            notes = read(d / "NOTES.md")
            m = re.match(r"#\s+(.+)", notes)
            name = m.group(1).strip() if m and "<" not in m.group(1) else slug.replace("_", " ").replace("-", " ").title()
            sol = runner.find_solution(d)
            probs.append({
                "path": rel, "name": name, "slug": slug, "contest": c, "year": year, "round": rnd,
                "solution": sol.name if sol else None,
                "hasNotes": bool(notes), "hasAnalysis": (d / "analysis.pdf").exists(),
                "cases": len(runner.find_cases(d)),
            })
    return probs


def diagnostic_items(body: str) -> list[dict]:
    items = []
    for line in body.splitlines():
        m = re.match(r"\s*\d+\.\s+\*\*(.+?)\*\*(.*)", line)
        if not m:
            continue
        title, rest = m.group(1), m.group(2)
        names = []
        if rest.startswith(":"):
            names = [n.strip() for n in re.findall(r"(?:^|,)\s*([A-Z][^(),]*?)\s*\(", rest[1:])]
        items.append({"title": title, "names": names or [title], "text": line.strip()})
    return items


def state() -> dict:
    log_md, skills_md, reading_md = (read(LEARNING / f) for f in ("log.md", "skills.md", "reading.md"))
    log = [r for r in parse_table(log_md) if any(r.values())]
    skill_secs = sections(skills_md)
    skills = parse_table(skill_secs.get("Topics", ""))
    reviews = [{"title": t, "body": b} for t, b in sections(skill_secs.get("Reviews", ""), 3).items()]
    read_secs = sections(reading_md)
    logged_names = [r.get("Problem", "") for r in log]

    def logged(*names):
        return [r for r in log if any(similar(r.get("Problem", ""), n) for n in names)]

    problems = find_problems()
    for p in problems:
        p["log"] = logged(p["name"], p["slug"])

    diag_key = next((k for k in read_secs if k.lower().startswith("diagnostic")), None)
    diag = diagnostic_items(read_secs.get(diag_key, "")) if diag_key else []
    for it in diag:
        it["problems"] = [{
            "name": n,
            "logged": bool(logged(n)),
            "repo": next((p["path"] for p in problems if similar(p["name"], n) or similar(p["slug"], n)), None),
        } for n in it["names"]]

    active = []
    for line in read_secs.get("Active", "").splitlines():
        m = re.match(r"- \[( |x|X)\]\s+(.*)", line)
        if m:
            active.append({"done": m.group(1) != " ", "text": m.group(2)})

    return {
        "today": date.today().isoformat(),
        "log": log, "skills": skills, "reviews": reviews,
        "reading": read_secs, "readingActive": active, "diagnostic": diag, "diagnosticTitle": diag_key,
        "problems": problems, "loggedNames": logged_names,
    }


# ---------- problem actions ----------

def problem_dir(rel: str) -> Path:
    d = (ROOT / rel).resolve()
    if ROOT not in d.parents or not (d / "statement.pdf").exists():
        raise ValueError(f"not a problem folder: {rel}")
    return d


def problem_detail(rel: str) -> dict:
    d = problem_dir(rel)
    sol = runner.find_solution(d)
    n_py = len([p for p in d.glob("*.py") if not p.name.startswith(".")])
    samples = []
    for inp in sorted((d / "sample").rglob("*.in")):
        ans = inp.with_suffix(".ans")
        samples.append({"label": inp.relative_to(d).as_posix(),
                        "input": inp.read_text(errors="replace")[:4000],
                        "answer": ans.read_text(errors="replace")[:4000] if ans.exists() else ""})
    return {
        "path": rel,
        "solution": sol.name if sol else None,
        "multiplePy": n_py > 1,
        "code": sol.read_text(encoding="utf-8") if sol else SOLUTION_TEMPLATE,
        "notes": read(d / "NOTES.md"),
        "notesTemplate": read(LEARNING / "templates" / "NOTES.md"),
        "samples": samples,
        "cases": [c.relative_to(d).as_posix() for c in runner.find_cases(d)],
    }


def save(rel: str, kind: str, content: str) -> dict:
    d = problem_dir(rel)
    if kind == "notes":
        target = d / "NOTES.md"
    elif kind == "solution":
        sol = runner.find_solution(d)
        target = sol or d / "solution.py"
    else:
        raise ValueError(kind)
    target.write_text(content.replace("\r\n", "\n"), encoding="utf-8")
    return {"saved": target.relative_to(ROOT).as_posix()}


def run_tests(rel: str, timeout: float) -> dict:
    d = problem_dir(rel)
    sol = runner.find_solution(d)
    if not sol:
        raise ValueError("Need exactly one .py file in the problem folder.")
    cmd = [sys.executable, str(sol)]
    return {"results": [runner.run_case(cmd, d, c, timeout) for c in runner.find_cases(d)]}


def exec_custom(rel: str, stdin: str, timeout: float) -> dict:
    d = problem_dir(rel)
    sol = runner.find_solution(d)
    if not sol:
        raise ValueError("Need exactly one .py file in the problem folder.")
    start = time.perf_counter()
    try:
        r = subprocess.run([sys.executable, str(sol)], input=stdin.encode(), capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"Timed out after {timeout:.0f}s", "rc": None, "time": timeout}
    return {"stdout": r.stdout.decode(errors="replace")[:100_000], "stderr": r.stderr.decode(errors="replace")[:20_000],
            "rc": r.returncode, "time": time.perf_counter() - start}


# ---------- HTTP ----------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj).encode(), "application/json")

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, b"forbidden", "text/plain")
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path == "/":
                return self._send(200, (ROOT / "tools" / "dashboard.html").read_bytes(), "text/html; charset=utf-8")
            if url.path == "/api/state":
                return self._json(state())
            if url.path == "/api/problem":
                return self._json(problem_detail(q["path"]))
            if url.path.startswith("/files/"):
                f = (ROOT / unquote(url.path[len("/files/"):])).resolve()
                if ROOT not in f.parents or not f.is_file() or f.suffix.lower() != ".pdf":
                    return self._send(404, b"not found", "text/plain")
                return self._send(200, f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream")
            self._send(404, b"not found", "text/plain")
        except Exception as e:  # surface errors to the UI
            self._json({"error": str(e)}, 400)

    def do_POST(self):
        # Custom header forces a CORS preflight (which we never answer), so other sites can't POST here.
        if not self._host_ok() or self.headers.get("X-Dashboard") != "1":
            return self._send(403, b"forbidden", "text/plain")
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            timeout = float(body.get("timeout", 20))
            if self.path == "/api/save":
                return self._json(save(body["path"], body["kind"], body["content"]))
            if self.path == "/api/run":
                return self._json(run_tests(body["path"], timeout))
            if self.path == "/api/exec":
                return self._json(exec_custom(body["path"], body.get("stdin", ""), timeout))
            self._send(404, b"not found", "text/plain")
        except Exception as e:
            self._json({"error": str(e)}, 400)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Dashboard at {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
