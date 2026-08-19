"""
Application-owned external tool paths.
"""
from __future__ import annotations

import hashlib
import os
import platform
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit


YT_DLP_SUMS_URL = (
    "https://github.com/yt-dlp/yt-dlp/releases/latest/download/SHA2-256SUMS"
)
MAX_CHECKSUM_BYTES = 1024 * 1024
MAX_YT_DLP_BYTES = 150 * 1024 * 1024


def get_app_support_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ClipCatcher"
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "ClipCatcher"
    return Path.home() / ".local" / "share" / "ClipCatcher"


def get_app_bin_dir(create: bool = True) -> Path:
    bin_dir = get_app_support_dir() / "bin"
    if create:
        bin_dir.mkdir(parents=True, exist_ok=True)
    return bin_dir


def executable_name(name: str) -> str:
    if sys.platform == "win32" and not name.endswith(".exe"):
        return f"{name}.exe"
    return name


def find_app_tool(name: str) -> Optional[str]:
    candidate = get_app_bin_dir(create=False) / executable_name(name)
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return str(candidate)
    return None


def install_app_tool_from_path(name: str, source_path: str) -> Optional[str]:
    source = Path(source_path)
    if not source.is_file():
        return None

    target = get_app_bin_dir(create=True) / executable_name(name)
    try:
        if source.resolve() == target.resolve():
            return str(target)
    except FileNotFoundError:
        pass

    try:
        shutil.copy2(source, target)
        current_mode = target.stat().st_mode
        target.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return str(target)
    except Exception as exc:
        print(f"[tool cache] failed to install {name}: {exc}")
        return None


def get_yt_dlp_asset_name() -> str:
    if sys.platform == "win32":
        return "yt-dlp.exe"
    if sys.platform == "darwin":
        return "yt-dlp_macos"
    if sys.platform.startswith("linux"):
        machine = platform.machine().lower()
        if machine in {"x86_64", "amd64"}:
            return "yt-dlp_linux"
        if machine in {"aarch64", "arm64"}:
            return "yt-dlp_linux_aarch64"
    return "yt-dlp"


def get_yt_dlp_download_url() -> str:
    asset_name = get_yt_dlp_asset_name()
    return f"https://github.com/yt-dlp/yt-dlp/releases/latest/download/{asset_name}"


def _is_official_download_url(url: str) -> bool:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    return (
        parts.scheme == "https"
        and (
            host == "github.com"
            or host.endswith(".githubusercontent.com")
            or host.endswith(".github.com")
        )
    )


def _download_bytes(url: str, max_bytes: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ClipCatcher yt-dlp updater"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        final_url = response.geturl()
        if not _is_official_download_url(final_url):
            raise RuntimeError("yt-dlp 다운로드가 신뢰할 수 없는 주소로 이동했습니다.")
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                declared_size = int(content_length)
            except ValueError as exc:
                raise RuntimeError("yt-dlp 다운로드 응답 크기가 올바르지 않습니다.") from exc
            if declared_size > max_bytes:
                raise RuntimeError("yt-dlp 다운로드 파일이 허용 크기를 초과했습니다.")

        chunks = []
        received = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            received += len(chunk)
            if received > max_bytes:
                raise RuntimeError("yt-dlp 다운로드 파일이 허용 크기를 초과했습니다.")
            chunks.append(chunk)
    return b"".join(chunks)


def _expected_checksum(checksum_data: bytes, asset_name: str) -> str:
    try:
        text = checksum_data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("yt-dlp 체크섬 파일 형식이 올바르지 않습니다.") from exc
    for line in text.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2 and parts[1].lstrip("*") == asset_name:
            digest = parts[0].lower()
            if len(digest) == 64 and all(char in "0123456789abcdef" for char in digest):
                return digest
    raise RuntimeError("yt-dlp 공식 체크섬을 찾지 못했습니다.")


def install_or_update_yt_dlp() -> str:
    """Install an official, checksum-verified yt-dlp standalone binary."""
    target = get_app_bin_dir(create=True) / executable_name("yt-dlp")
    tmp_target = target.with_name(f"{target.stem}.download{target.suffix}")
    url = get_yt_dlp_download_url()
    asset_name = get_yt_dlp_asset_name()

    try:
        checksum_data = _download_bytes(YT_DLP_SUMS_URL, MAX_CHECKSUM_BYTES)
        expected_digest = _expected_checksum(checksum_data, asset_name)
        data = _download_bytes(url, MAX_YT_DLP_BYTES)
        actual_digest = hashlib.sha256(data).hexdigest()
        if actual_digest != expected_digest:
            raise RuntimeError("yt-dlp 다운로드 파일의 체크섬이 일치하지 않습니다.")

        with open(tmp_target, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        current_mode = tmp_target.stat().st_mode
        tmp_target.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        version_check = subprocess.run(
            [str(tmp_target), "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
        if version_check.returncode != 0 or not version_check.stdout.strip():
            raise RuntimeError("다운로드한 yt-dlp 실행 파일을 검증하지 못했습니다.")
        os.replace(tmp_target, target)
    finally:
        if tmp_target.exists():
            try:
                tmp_target.unlink()
            except OSError:
                pass

    return str(target)
