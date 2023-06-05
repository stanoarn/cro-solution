#!/usr/bin/env python

import argparse
import datetime
import pathlib
import json
from os import environ, devnull
from sys import stderr
from dataclasses import dataclass, asdict

VERSION = "1.0.0"


@dataclass
class Entry:
    date: datetime.date
    text: str


@dataclass
class FailureRecord:
    file: pathlib.Path
    reason: str


def as_entry(dct: dict) -> Entry:
    try:
        return Entry(date=str_to_date(dct["date"]), text=dct["text"])
    except KeyError or ValueError:
        raise json.JSONDecodeError


def str_to_date(string: str) -> datetime.date:
    return datetime.date.fromisoformat(string)


def get_week(in_date: datetime.date) -> int:
    """Returns the week number for a date. The values returned can be between 1 and 54."""
    return int(in_date.strftime("%W")) + (1 if datetime.date(in_date.year, 1, 1).weekday() != 0 else 0)


class FailedManager:
    """
    Handles failed transfers by writing the names of files that failed to transfer into
    a file.
    """

    def __init__(self, file_name: pathlib.Path) -> None:
        self.list = []
        self.file = open(file_name, mode="wt")

    def __del__(self) -> None:
        self.file.close()
        print(f"A total of {self.count} transfers has failed.", file=stderr)
        print(f"The paths to offending files have benn written into {self.file.name}.", file=stderr)

    def handle_failure(self, failed_file: pathlib.Path, reason: str) -> None:
        print(f"Transfer of {failed_file.name} failed: {reason}\nAdding it to the list for manual review", file=stderr)
        record = FailureRecord(file=failed_file, reason=reason)
        self.list.append(record)
        self.file.write(json.dumps(asdict(record), indent=4, sort_keys=True, default=str))

    @property
    def count(self) -> int:
        return len(self.list)


def parse_args() -> (pathlib.Path, pathlib.Path, pathlib.Path, bool):
    parser = argparse.ArgumentParser(
        description="The program moves JSON files from the directory specifies by the --input option to"
        " the directory specified by the --output option, creating an appropriate directory structure."
        " Unless --write is specified, the move is not actually performed."
    )
    parser.add_argument("-v", "--version", action="version", version="1.0.0")
    parser.add_argument(
        "-i",
        "--input",
        type=pathlib.Path,
        action="store",
        help="Input directory containing the JSON files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        action="store",
        help="Output directory to move the files to",
    )
    parser.add_argument(
        "-f",
        "--failed",
        type=pathlib.Path,
        action="store",
        help="File to store information about failed transfers in. Default is platform equivalent of /dev/null",
        default=devnull,
    )
    parser.add_argument(
        "-w",
        "--write",
        action="store_true",
        help="Unless specified, the write is not performed (dry run)",
    )

    # -h / --help is implicitly defined

    args = parser.parse_args()
    indir, outdir, failed, write = args.input, args.output, args.failed, args.write

    try:
        if indir is None:
            indir = pathlib.Path(environ["SOURCE_DIRECTORY"])
        if outdir is None:
            outdir = pathlib.Path(environ["TARGET_DIRECTORY"])
    except KeyError:
        print("Input or output missing!", file=stderr)
        exit(1)

    return indir, outdir, failed, write


def try_parse(file: pathlib.Path, fman: FailedManager) -> Entry or None:
    """
    Tries to parse json as an entry.
    In case of failure returns None and logs the incident
    """
    with open(file, mode="r") as f:
        try:
            entry = json.load(f, object_hook=as_entry)
        except json.JSONDecodeError:
            fman.handle_failure(file, "Malformed JSON")
            return None

        # attempt to parse the filename date
        fname = file.parts[-1]
        fname_date = fname.split("_")[0]
        try:
            file_date = str_to_date(fname_date)
        except ValueError:
            fman.handle_failure(file, "Malformed filename")
            return None

        # check if the dates match
        if file_date != entry.date:
            fman.handle_failure(file, "Date mismatch")
            return None

        return entry


def main() -> None:
    indir, outdir, failed, write = parse_args()
    fman = FailedManager(failed)
    total_files = 0

    for file in indir.glob("*.json"):
        total_files += 1
        entry = try_parse(file, fman)
        if entry is None:
            continue

        # determine the year and week
        # January 1st is always a part of the first week of the year.
        # Slightly breaks the assignment because leap years starting
        # with a Monday have 54 weeks
        year, week = entry.date.year, get_week(entry.date)
        output_path = outdir / str(year) / f"W{week:02d}"
        outfile = output_path / "-".join(file.parts[-1].split("-")[1:])
        info_dict = {
            "source": str(file),
            "target": str(outfile),
        }

        # print transfer info and, if instructed to, perform the move
        print(json.dumps(info_dict))
        if write:
            try:
                output_path.mkdir(exist_ok=True, parents=True)
                file.rename(outfile)  # will not work across devices, also overwrites existing data
            except OSError as e:
                fman.handle_failure(file, str(e))
                continue

    print(
        f"{'Success' if fman.count == 0 else 'Failure'}: processed {total_files - fman.count}/{total_files} files",
        file=stderr,
    )
    exit(fman.count)


if __name__ == "__main__":
    main()
