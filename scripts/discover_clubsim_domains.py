#!/usr/bin/env python3
"""Discover Club Sim domain candidates from public, non-authenticated sources."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import html
import ipaddress
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "clubsim_candidates.tsv"
USER_AGENT = (
    "quantumultx-clubsim-rules-discovery/1.0 "
    "(+https://github.com/bluelittlerain/quantumultx-bybit-rules)"
)
NETWORK_TIMEOUT_SECONDS = 30
MAX_TEXT_BYTES = 12 * 1024 * 1024
MAX_APK_BYTES = 250 * 1024 * 1024

OFFICIAL_PAGES = (
    "https://www.clubsim.com.hk/",
    "https://www.clubsim.com.hk/en/login",
    "https://www.clubsim.com.hk/en/support",
    "https://www.clubsim.com.hk/en/quick-start",
    "https://www.clubsim.com.hk/clsecomm/selection",
    "https://www.clubsim.com.hk/clsweb/faq",
)
OFFICIAL_APK_URL = "https://www.clubsim.com.hk/api/apk/download"
COMMUNITY_RULE_URL = (
    "https://raw.githubusercontent.com/ClearLuv/iOS_collecton/"
    "main/Rule/ClubSim.list"
)
EXPECTED_PACKAGE = "com.pccw.clubsim"

NETWORK_DOMAINS = frozenset(
    {
        "csl.prod.ondemandconnectivity.com",
        "hhk.prod.ondemandconnectivity.com",
        "epdg.epc.mnc000.mcc454.pub.3gppnetwork.org",
        "ss.epdg.epc.mnc000.mcc454.pub.3gppnetwork.org",
        "ss.epdg.epc.geo.mnc000.mcc454.pub.3gppnetwork.org",
    }
)
SHARED_ROOTS = frozenset(
    {
        "akamai.net",
        "akamaiedge.net",
        "1010-lifestyle.com",
        "1010.com.hk",
        "amazon.com",
        "amazonaws.com",
        "apple.com",
        "appgallery.huawei.com",
        "appsflyer.com",
        "bing.com",
        "bit.ly",
        "cahk.hk",
        "cdn-apple.com",
        "citibank.com.hk",
        "cloudflare.com",
        "cloudfront.net",
        "digitpepper.com",
        "doubleclick.net",
        "facebook.com",
        "facebook.net",
        "fb.me",
        "firebaseapp.com",
        "firebaseio.com",
        "feross.org",
        "github.io",
        "github.com",
        "goo.gl",
        "google-analytics.com",
        "google.com",
        "googleapis.com",
        "googleusercontent.com",
        "googletagmanager.com",
        "gstatic.com",
        "hkcsl-5g.com",
        "hkcsl.com",
        "hkt.com",
        "hktcare.com",
        "icloud.com",
        "instagram.com",
        "i-guard.hk",
        "klook.com",
        "mastercard.com",
        "momentjs.com",
        "mozilla.org",
        "mzstatic.com",
        "nowe.com",
        "nowe.hk",
        "nxtomo.com",
        "nxtomogames.com",
        "onelink.to",
        "page.link",
        "paypal.com",
        "pccw.com",
        "play.google.com",
        "reactjs.org",
        "recaptcha.net",
        "sentry.io",
        "stripe.com",
        "tapngo.com.hk",
        "theclub.com.hk",
        "unimhk.com",
        "valueplatforms.com",
        "visa.com",
        "viu.com",
        "w3.org",
        "whatsapp.com",
        "youtube.com",
        "youtube-nocookie.com",
    }
)
ANALYTICS_OR_SHARED_HOSTS = frozenset(
    {
        "api.qrserver.com",
        "bat.bing.com",
        "connect.facebook.net",
        "fonts.googleapis.com",
        "www.google-analytics.com",
        "www.googletagmanager.com",
    }
)

URL_RE = re.compile(
    r"(?i)(?:https?|wss?)://[a-z0-9._~%!$&'()*+,;=:@/?#\[\]-]+"
)
ATTR_RE = re.compile(
    r"""(?i)\b(?:src|href)\s*=\s*["']([^"'<>]+)["']"""
)
DOMAIN_RE = re.compile(
    rb"(?i)(?<![a-z0-9_-])"
    rb"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    rb"[a-z]{2,24}(?![a-z0-9_-])"
)


class DiscoveryError(RuntimeError):
    """A discovery source failed without changing the candidate file."""


@dataclasses.dataclass(frozen=True)
class Candidate:
    domain: str
    rule_type: str
    scope: str
    status: str
    source: str
    evidence: str
    risk: str
    notes: str

    def tsv(self) -> str:
        values = dataclasses.astuple(self)
        return "\t".join(_clean_tsv_field(value) for value in values)


@dataclasses.dataclass(frozen=True)
class ApkReport:
    source: str
    version: str
    version_code: str
    size: int
    sha256: str
    package_verified: bool
    domains: frozenset[str]


@dataclasses.dataclass
class DiscoveryReport:
    candidates: list[Candidate]
    fetched_pages: int
    fetched_scripts: int
    raw_occurrences: int
    apk: ApkReport | None


def _clean_tsv_field(value: object) -> str:
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")


def sanitize_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(html.unescape(url.strip()))
    if parsed.scheme.lower() not in {"http", "https", "ws", "wss"}:
        raise DiscoveryError(f"Unsupported public URL scheme: {parsed.scheme!r}")
    if not parsed.hostname:
        raise DiscoveryError("Public URL has no host")
    host = parsed.hostname.lower().rstrip(".")
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path or "/"
    return urllib.parse.urlunsplit(
        (parsed.scheme.lower(), f"{host}{port}", path, "", "")
    )


def normalize_host(host: str) -> str:
    value = host.strip().rstrip(".").lower()
    if not value or "/" in value or "?" in value or "#" in value:
        raise DiscoveryError(f"Invalid host candidate: {host!r}")
    return value


def is_public_domain_candidate(host: str) -> bool:
    host = host.strip().rstrip(".").lower()
    if host == "localhost" or "." not in host:
        return False
    try:
        parsed_ip = ipaddress.ip_address(host)
    except ValueError:
        parsed_ip = None
    if parsed_ip is not None:
        return False
    labels = host.split(".")
    return all(
        label
        and len(label) <= 63
        and re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
        for label in labels
    ) and bool(re.fullmatch(r"[a-z]{2,24}", labels[-1]))


def _is_under(host: str, root: str) -> bool:
    return host == root or host.endswith(f".{root}")


def classify_host(host: str, source: str, *, evidence: str) -> Candidate:
    host = normalize_host(host)
    source = sanitize_url(source)
    if _is_under(host, "clubsim.com.hk"):
        return Candidate(
            domain="clubsim.com.hk",
            rule_type="HOST-SUFFIX",
            scope="prepaid-app",
            status="confirmed",
            source=source,
            evidence=evidence,
            risk="low",
            notes="Official Club Sim root; covers relative web and API paths.",
        )
    if host == "clubsim.page.link":
        return Candidate(
            domain=host,
            rule_type="HOST",
            scope="prepaid-app",
            status="confirmed",
            source=source,
            evidence=evidence,
            risk="low",
            notes="Dedicated Club Sim dynamic-link hostname; the page.link root is excluded.",
        )
    if host in NETWORK_DOMAINS:
        return Candidate(
            domain=host,
            rule_type="HOST",
            scope="network",
            status="optional",
            source=source,
            evidence=evidence,
            risk="medium",
            notes="Optional eSIM, ePDG or operator network service; not an App API.",
        )
    if host in {"www.clubsim.com", "clubsim.com"}:
        return Candidate(
            domain=host,
            rule_type="HOST",
            scope="unknown",
            status="excluded",
            source=source,
            evidence=evidence,
            risk="medium",
            notes="Stale script link is paired with an actual clubsim.com.hk destination.",
        )
    if host in ANALYTICS_OR_SHARED_HOSTS or any(
        _is_under(host, root) for root in SHARED_ROOTS
    ):
        return Candidate(
            domain=host,
            rule_type="HOST",
            scope="shared",
            status="excluded",
            source=source,
            evidence=evidence,
            risk="high",
            notes="Shared identity, analytics, platform, telecom-group or infrastructure host.",
        )
    return Candidate(
        domain=host,
        rule_type="HOST",
        scope="unknown",
        status="needs-review",
        source=source,
        evidence=evidence,
        risk="medium",
        notes="Public reference found, but Club Sim exclusivity is not established.",
    )


def extract_urls(text: str, base_url: str) -> list[str]:
    normalized = html.unescape(text).replace("\\/", "/")
    urls = [match.group(0).rstrip(".,;)}]") for match in URL_RE.finditer(normalized)]
    for match in ATTR_RE.finditer(normalized):
        value = match.group(1).strip()
        if value.startswith(("javascript:", "data:", "mailto:", "tel:", "#")):
            continue
        urls.append(urllib.parse.urljoin(base_url, value))
    sanitized: set[str] = set()
    for url in urls:
        try:
            sanitized.add(sanitize_url(url))
        except (DiscoveryError, ValueError):
            continue
    return sorted(sanitized)


def extract_same_site_scripts(text: str, base_url: str) -> list[str]:
    base_host = urllib.parse.urlsplit(base_url).hostname
    scripts: set[str] = set()
    for match in ATTR_RE.finditer(html.unescape(text)):
        value = match.group(1).strip()
        path = urllib.parse.urlsplit(value).path.lower()
        if not path.endswith(".js"):
            continue
        resolved = urllib.parse.urljoin(base_url, value)
        if urllib.parse.urlsplit(resolved).hostname == base_host:
            scripts.add(resolved)
    return sorted(scripts)


def validate_public_text(text: str, source: str, content_type: str = "") -> None:
    if not text or not text.strip():
        raise DiscoveryError(f"Public source was empty: {sanitize_url(source)}")
    sample = text.lstrip().lower()[:4096]
    error_markers = (
        "<title>access denied",
        "<title>forbidden",
        "<title>captcha",
        "cf-chl-captcha",
        "request was rejected",
    )
    if any(marker in sample for marker in error_markers):
        raise DiscoveryError(
            f"Public source returned an error or challenge page: {sanitize_url(source)}"
        )
    if "javascript" in content_type or source.lower().endswith(".js"):
        if sample.startswith(("<!doctype html", "<html")):
            raise DiscoveryError(
                f"JavaScript source returned HTML: {sanitize_url(source)}"
            )


def fetch_text(url: str) -> tuple[str, str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html, application/javascript, text/plain, */*;q=0.1",
        },
    )
    try:
        with urllib.request.urlopen(
            request, timeout=NETWORK_TIMEOUT_SECONDS
        ) as response:
            data = response.read(MAX_TEXT_BYTES + 1)
            final_url = response.geturl()
            content_type = response.headers.get_content_type()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise DiscoveryError(
            f"Unable to fetch public source {sanitize_url(url)}: {exc}"
        ) from exc
    if len(data) > MAX_TEXT_BYTES:
        raise DiscoveryError(f"Public text source is unexpectedly large: {url}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DiscoveryError(f"Public source is not UTF-8: {url}") from exc
    validate_public_text(text, final_url, content_type)
    return text, final_url, content_type


def parse_community_rules(text: str, source: str) -> list[Candidate]:
    validate_public_text(text, source, "text/plain")
    candidates: list[Candidate] = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 2 or parts[0].upper() not in {
            "DOMAIN",
            "DOMAIN-SUFFIX",
            "HOST",
            "HOST-SUFFIX",
        }:
            continue
        candidates.append(
            classify_host(
                parts[1],
                source,
                evidence="Current public ClubSim network rule.",
            )
        )
    if len(candidates) < 5:
        raise DiscoveryError(
            f"Community source has only {len(candidates)} usable rules"
        )
    return candidates


def _deduplicate(candidates: Iterable[Candidate]) -> list[Candidate]:
    status_order = {
        "confirmed": 0,
        "optional": 1,
        "excluded": 2,
        "needs-review": 3,
    }
    unique: dict[str, Candidate] = {}
    for candidate in candidates:
        current = unique.get(candidate.domain)
        if current is None or status_order[candidate.status] < status_order[current.status]:
            unique[candidate.domain] = candidate
    return sorted(unique.values(), key=lambda item: item.domain.casefold())


def discover_candidates(
    *,
    fetcher: Callable[[str], tuple[str, str, str]] = fetch_text,
    pages: Sequence[str] = OFFICIAL_PAGES,
) -> DiscoveryReport:
    candidates: list[Candidate] = []
    scripts: set[str] = set()
    raw_occurrences = 0
    for page_url in pages:
        text, final_url, _ = fetcher(page_url)
        for url in extract_urls(text, final_url):
            host = urllib.parse.urlsplit(url).hostname
            if not host or not is_public_domain_candidate(host):
                continue
            raw_occurrences += 1
            candidates.append(
                classify_host(
                    host,
                    final_url,
                    evidence="Referenced by a Club Sim official public page.",
                )
            )
        scripts.update(extract_same_site_scripts(text, final_url))

    for script_url in sorted(scripts):
        text, final_url, _ = fetcher(script_url)
        for url in extract_urls(text, final_url):
            host = urllib.parse.urlsplit(url).hostname
            if not host or not is_public_domain_candidate(host):
                continue
            raw_occurrences += 1
            candidates.append(
                classify_host(
                    host,
                    final_url,
                    evidence="Referenced by a Club Sim official public script.",
                )
            )

    upstream_text, upstream_final, _ = fetcher(COMMUNITY_RULE_URL)
    network_candidates = parse_community_rules(upstream_text, upstream_final)
    candidates.extend(network_candidates)
    raw_occurrences += len(network_candidates)
    return DiscoveryReport(
        candidates=_deduplicate(candidates),
        fetched_pages=len(pages),
        fetched_scripts=len(scripts),
        raw_occurrences=raw_occurrences,
        apk=None,
    )


def _stream_contains(handle: object, needle: bytes) -> bool:
    overlap = max(0, len(needle) - 1)
    previous = b""
    while True:
        chunk = handle.read(1024 * 1024)
        if not chunk:
            return False
        block = previous + chunk
        if needle in block:
            return True
        previous = block[-overlap:] if overlap else b""


def _domains_from_zip_member(handle: object) -> set[str]:
    domains: set[str] = set()
    overlap = 256
    previous = b""
    while True:
        chunk = handle.read(1024 * 1024)
        if not chunk:
            break
        block = previous + chunk
        for match in DOMAIN_RE.finditer(block):
            try:
                domains.add(normalize_host(match.group(0).decode("ascii")))
            except (UnicodeDecodeError, DiscoveryError):
                continue
        previous = block[-overlap:]
    return domains


def inspect_apk_file(path: Path, source_url: str) -> ApkReport:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise DiscoveryError("Official APK download is not a valid APK/ZIP") from exc

    package_verified = False
    domains: set[str] = set()
    scan_names = [
        info.filename
        for info in archive.infolist()
        if info.filename == "AndroidManifest.xml"
        or info.filename.endswith(".dex")
        or info.filename.startswith(("assets/", "res/raw/", "res/xml/"))
    ]
    for name in scan_names:
        with archive.open(name) as member:
            if _stream_contains(member, EXPECTED_PACKAGE.encode("ascii")):
                package_verified = True
                break
    if not package_verified:
        archive.close()
        raise DiscoveryError(
            f"Official APK did not contain expected package marker {EXPECTED_PACKAGE}"
        )
    for name in scan_names:
        with archive.open(name) as member:
            domains.update(_domains_from_zip_member(member))
    archive.close()

    clean_source = sanitize_url(source_url)
    filename = urllib.parse.unquote(Path(urllib.parse.urlsplit(source_url).path).name)
    version_match = re.search(r"(?i)\bv(\d+(?:\.\d+)+)", filename)
    code_match = re.search(r"\[(\d{3,})\]", filename)
    return ApkReport(
        source=clean_source,
        version=version_match.group(1) if version_match else "not advertised",
        version_code=code_match.group(1) if code_match else "not advertised",
        size=path.stat().st_size,
        sha256=digest.hexdigest().upper(),
        package_verified=True,
        domains=frozenset(domains),
    )


def download_and_inspect_apk(url: str = OFFICIAL_APK_URL) -> ApkReport:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.android.package-archive, */*;q=0.1",
        },
    )
    try:
        response = urllib.request.urlopen(request, timeout=NETWORK_TIMEOUT_SECONDS)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise DiscoveryError(f"Unable to download official APK: {exc}") from exc
    final_url = response.geturl()
    final_host = urllib.parse.urlsplit(final_url).hostname
    if final_host not in {"clubsim.com.hk", "www.clubsim.com.hk"}:
        response.close()
        raise DiscoveryError("Official APK redirected outside the Club Sim domain")
    content_length = response.headers.get("Content-Length")
    if content_length and int(content_length) > MAX_APK_BYTES:
        response.close()
        raise DiscoveryError("Official APK exceeds the configured size limit")

    with tempfile.TemporaryDirectory(prefix="clubsim-apk-") as temp_dir:
        apk_path = Path(temp_dir) / "clubsim.apk"
        size = 0
        with apk_path.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_APK_BYTES:
                    response.close()
                    raise DiscoveryError("Official APK exceeded the size limit")
                output.write(chunk)
        response.close()
        if not size:
            raise DiscoveryError("Official APK download was empty")
        return inspect_apk_file(apk_path, final_url)


def merge_apk_candidates(
    report: DiscoveryReport, apk_report: ApkReport
) -> DiscoveryReport:
    candidates = list(report.candidates)
    for host in apk_report.domains:
        if not is_public_domain_candidate(host):
            continue
        candidates.append(
            classify_host(
                host,
                apk_report.source,
                evidence="String found by static inspection of the official APK.",
            )
        )
    return DiscoveryReport(
        candidates=_deduplicate(candidates),
        fetched_pages=report.fetched_pages,
        fetched_scripts=report.fetched_scripts,
        raw_occurrences=report.raw_occurrences + len(apk_report.domains),
        apk=apk_report,
    )


def render_candidates(candidates: Sequence[Candidate]) -> str:
    header = (
        "domain\trule_type\tscope\tstatus\tsource\tevidence\trisk\tnotes"
    )
    return "\n".join([header, *[candidate.tsv() for candidate in candidates], ""])


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def resolve_output(value: str | None) -> Path:
    path = Path(value).resolve() if value else DEFAULT_OUTPUT.resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise DiscoveryError("Candidate output must stay inside this repository") from exc
    return path


def print_summary(report: DiscoveryReport, *, verbose: bool = False) -> None:
    counts: dict[str, int] = {}
    for candidate in report.candidates:
        counts[candidate.status] = counts.get(candidate.status, 0) + 1
    print(f"Official pages fetched: {report.fetched_pages}")
    print(f"Official scripts fetched: {report.fetched_scripts}")
    print(f"Raw domain occurrences: {report.raw_occurrences}")
    print(f"Unique candidates: {len(report.candidates)}")
    for status in ("confirmed", "optional", "excluded", "needs-review"):
        print(f"{status}: {counts.get(status, 0)}")
    if report.apk:
        print(f"APK source: {report.apk.source}")
        print(f"APK version: {report.apk.version}")
        print(f"APK version code: {report.apk.version_code}")
        print(f"APK bytes: {report.apk.size}")
        print(f"APK SHA-256: {report.apk.sha256}")
        print(f"APK package verified: {'yes' if report.apk.package_verified else 'no'}")
    if verbose:
        for candidate in report.candidates:
            print(
                f"{candidate.status:12} {candidate.scope:12} "
                f"{candidate.rule_type:11} {candidate.domain}"
            )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover Club Sim domains from public sources"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="check public sources without writing the candidate file",
    )
    parser.add_argument(
        "--output",
        help="candidate TSV path inside the repository",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="print each classified candidate"
    )
    parser.add_argument(
        "--no-apk",
        action="store_true",
        help="skip the large official APK static inspection",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = discover_candidates()
        if not args.no_apk:
            report = merge_apk_candidates(report, download_and_inspect_apk())
        print_summary(report, verbose=args.verbose)
        if not args.check:
            output = resolve_output(args.output)
            atomic_write(output, render_candidates(report.candidates))
            print(f"Candidate report updated: {output.relative_to(ROOT)}")
        return 0
    except DiscoveryError as exc:
        print(f"ClubSim discovery failed safely: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
