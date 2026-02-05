#!/usr/bin/env python3
"""
Check Fern-hosted docs routes for reachability.

Source of truth: PREVIEW_URL/sitemap.xml

Fails the process if any sitemap URL:
- redirects to a URL containing `error=true` (Fern crash loop pattern), or
- returns HTTP >= 400, or
- raises an exception during fetch
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Iterable, Literal
from urllib.parse import urlparse
from pathlib import Path

import requests


Kind = Literal["redirect_error", "http_error", "exception"]


@dataclass(frozen=True)
class Issue:
    kind: Kind
    url: str
    status: int | None = None
    location: str | None = None
    error: str | None = None


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check Fern docs sitemap URLs are reachable.")
    p.add_argument("--preview-url", required=True, help="Fern docs preview base URL (https://...docs.buildwithfern.com)")
    p.add_argument(
        "--report-path",
        default="docs-route-check-report.md",
        help="Markdown report output path (default: docs-route-check-report.md)",
    )
    return p.parse_args(argv)


def _normalize_base(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        raise ValueError(f"preview_url must start with http(s): {url}")
    return url.rstrip("/")


def _extract_locs_from_sitemap(xml_text: str) -> list[str]:
    # Namespaces vary; handle both namespaced and non-namespaced <loc>.
    root = ET.fromstring(xml_text)
    locs: list[str] = []
    for el in root.iter():
        if el.tag.endswith("loc") and el.text:
            locs.append(el.text.strip())
    return locs


def _same_origin_urls(base: str, urls: Iterable[str]) -> list[str]:
    base_origin = urlparse(base).netloc
    out: list[str] = []
    for u in sorted(set(urls)):
        pu = urlparse(u)
        if pu.scheme not in ("http", "https"):
            continue
        if pu.netloc != base_origin:
            continue
        out.append(u)
    return out


def _check_one(sess: requests.Session, url: str, timeout_seconds: float, user_agent: str) -> Issue | None:
    try:
        r = sess.get(
            url,
            allow_redirects=False,
            timeout=timeout_seconds,
            headers={"user-agent": user_agent},
        )
        loc = r.headers.get("location", "")
        if r.status_code in (301, 302, 303, 307, 308) and "error=true" in (loc or ""):
            return Issue(kind="redirect_error", url=url, status=r.status_code, location=loc or None)
        if r.status_code >= 400:
            return Issue(kind="http_error", url=url, status=r.status_code, location=loc or None)
        return None
    except Exception as e:
        return Issue(kind="exception", url=url, error=f"{type(e).__name__}: {e}")


def _render_report(base: str, sitemap_url: str, checked_count: int, issues: list[Issue]) -> str:
    redir = [i for i in issues if i.kind == "redirect_error"]
    http_err = [i for i in issues if i.kind == "http_error"]
    exc = [i for i in issues if i.kind == "exception"]

    lines: list[str] = []
    lines.append(f"## Docs route check for `{base}`")
    lines.append("")
    lines.append(f"- Sitemap: `{sitemap_url}`")
    lines.append(f"- Total sitemap URLs checked: **{checked_count}**")
    lines.append(f"- Redirect loops (`?error=true`): **{len(redir)}**")
    lines.append(f"- HTTP errors (>= 400): **{len(http_err)}**")
    lines.append(f"- Exceptions: **{len(exc)}**")
    lines.append("")

    if redir:
        lines.append("### Redirect loops (`?error=true`)")
        lines.append("")
        lines.append("| URL | Status | Location |")
        lines.append("|---|---:|---|")
        for i in sorted(redir, key=lambda x: x.url):
            lines.append(f"| `{i.url}` | {i.status} | `{i.location or ''}` |")
        lines.append("")

    if http_err:
        lines.append("### HTTP errors")
        lines.append("")
        lines.append("| URL | Status | Location |")
        lines.append("|---|---:|---|")
        for i in sorted(http_err, key=lambda x: x.url):
            lines.append(f"| `{i.url}` | {i.status} | `{i.location or ''}` |")
        lines.append("")

    if exc:
        lines.append("### Exceptions")
        lines.append("")
        lines.append("| URL | Error |")
        lines.append("|---|---|")
        for i in sorted(exc, key=lambda x: x.url):
            safe = (i.error or "").replace("\n", " ")[:240]
            lines.append(f"| `{i.url}` | `{safe}` |")
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    try:
        base = _normalize_base(args.preview_url)
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 2

    # Keep behavior/config minimal and workflow-aligned:
    # - sitemap path is fixed
    # - concurrency and per-request timeouts are fixed
    sitemap_url = f"{base}/sitemap.xml"
    workers = 25
    timeout_seconds = 15.0
    user_agent = "label-studio-client-generator/docs-route-check"

    sess = requests.Session()
    try:
        r = sess.get(sitemap_url, timeout=30, headers={"user-agent": user_agent})
    except Exception as e:
        print(f"Failed to fetch sitemap at {sitemap_url}: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    if r.status_code != 200:
        print(f"Sitemap fetch failed: {sitemap_url} returned HTTP {r.status_code}", file=sys.stderr)
        return 1

    try:
        locs = _extract_locs_from_sitemap(r.text)
    except Exception as e:
        print(f"Failed to parse sitemap XML from {sitemap_url}: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    urls = _same_origin_urls(base, locs)
    if not urls:
        print(f"No URLs to check after filtering from sitemap: {sitemap_url}", file=sys.stderr)
        return 1

    issues: list[Issue] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_check_one, sess, u, timeout_seconds, user_agent) for u in urls]
        for f in as_completed(futs):
            res = f.result()
            if res is not None:
                issues.append(res)

    report = _render_report(base=base, sitemap_url=sitemap_url, checked_count=len(urls), issues=issues)
    Path(args.report_path).write_text(report)
    print(report)

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

