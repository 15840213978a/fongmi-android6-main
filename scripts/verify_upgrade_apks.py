#!/usr/bin/env python3
"""Verify actual release APK identity, platform, ABI, and existing signing key."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile


def output(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)


def certificate_digest(text):
    # Build Tools 37 prints "V2 Signer:" instead of the older "Signer #1".
    # A certificate may be repeated for multiple verified signature schemes.
    if not re.search(r"(?m)^Number of signers: 1$", text):
        raise RuntimeError("Expected exactly one APK signer")
    digests = {value.lower() for value in re.findall(
        r"(?m)^(?:Signer #\d+|V[\d.]+ Signer[^:\r\n]*):? certificate SHA-256 digest: ([0-9a-fA-F]{64})$",
        text)}
    if len(digests) != 1:
        raise RuntimeError("Missing or inconsistent APK signing certificates")
    return digests.pop()


def signer(apksigner, apk):
    text = output(str(apksigner), "verify", "--verbose", "--print-certs", str(apk))
    return certificate_digest(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-tools", type=Path, required=True)
    parser.add_argument("--previous-apk", type=Path, required=True)
    args = parser.parse_args()
    bt = args.build_tools
    expected_signer = signer(bt / "apksigner", args.previous_apk)
    expected = {f"{flavor}-{abi.replace('-', '_')}-b6.apk": abi
                for flavor in ("mobile", "leanback")
                for abi in ("arm64-v8a", "armeabi-v7a")}
    actual = {p.name for p in Path("dist").glob("*.apk")}
    if actual != set(expected):
        raise RuntimeError(f"Unexpected APK set: {sorted(actual)}")
    for name, abi in expected.items():
        apk = Path("dist") / name
        badging = output(str(bt / "aapt2"), "dump", "badging", str(apk))
        for pattern in (r"package: name='com\.fongmi\.android\.tv\.b6'",
                        r"versionCode='568'", r"versionName='5\.6\.8'", r"(?m)^sdkVersion:'24'$"):
            if not re.search(pattern, badging):
                raise RuntimeError(f"APK identity/platform mismatch ({pattern}): {apk}")
        if signer(bt / "apksigner", apk) != expected_signer:
            raise RuntimeError(f"Signing key differs from installed 5.6.3: {apk}")
        with ZipFile(apk) as archive:
            abis = {p.split('/')[1] for p in archive.namelist() if p.startswith('lib/') and p.endswith('.so')}
            if abis != {abi}:
                raise RuntimeError(f"ABI mismatch {abis}: {apk}")
        print(f"Verified {name}: 5.6.8 (568), Android 7+, {abi}, existing signing key")
    meta = {"name": "5.6.8", "code": 568, "minSdk": 24,
            "desc": "升级至 5.6.8，最低 Android 7.0；保留 b6 包名和签名。"}
    for flavor in ("mobile", "leanback"):
        (Path("dist") / f"{flavor}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
