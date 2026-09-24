#!/usr/bin/env python3

import argparse
import re
from pathlib import Path

SUPPORTED_VERSIONS = {"0xb0", "0x86"}
SECTION_PATTERN = re.compile(r"(?m)^config\s+omci\s+(['\"])line0_omci\1\s*$")
OPTION_PATTERN = re.compile(r"(?m)^([ \t]*)option\s+omcc_version\s+(['\"])[^'\"]*\2([ \t]*(?:#.*)?)$")


def set_omcc_version(text: str, version: str) -> str:
    sections = list(SECTION_PATTERN.finditer(text))
    if len(sections) != 1:
        raise ValueError(f"expected one line0_omci section, found {len(sections)}")

    section_start = sections[0].end()
    next_section = re.search(r"(?m)^config\s+", text[section_start:])
    section_end = (
        section_start + next_section.start()
        if next_section is not None
        else len(text)
    )
    body = text[section_start:section_end]

    options = list(OPTION_PATTERN.finditer(body))
    if len(options) > 1:
        raise ValueError(f"expected at most one omcc_version option, found {len(options)}")

    if options:
        option = options[0]
        replacement = f"{option.group(1)}option omcc_version '{version}'{option.group(3)}"
        body = body[: option.start()] + replacement + body[option.end() :]
    else:
        if body and not body.endswith("\n"):
            body += "\n"
        body += f"\toption omcc_version '{version}'\n"

    return text[:section_start] + body + text[section_end:]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Set the default OMCC compatibility version in a PonWrt UCI file."
    )
    parser.add_argument("config", type=Path, help="path to the pon UCI configuration")
    parser.add_argument("version", choices=sorted(SUPPORTED_VERSIONS))
    args = parser.parse_args()

    original = args.config.read_text(encoding="utf-8")
    updated = set_omcc_version(original, args.version)
    if updated == original:
        print(f"{args.config}: omcc_version is already {args.version}")
        return

    args.config.write_text(updated, encoding="utf-8")
    print(f"{args.config}: set omcc_version to {args.version}")


if __name__ == "__main__":
    main()
