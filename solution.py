#!/usr/bin/env python

import argparse
import datetime
import pathlib
import json
from os import environ, devnull
from sys import stderr

VERSION = "1.0.0"
ROOT = "/home/arnold/builds/assignment"


def as_entry(dct: dict) -> dict or None:
    try:
        return {"date": str_to_date(dct["date"]), "text": dct["text"]}
    except KeyError or ValueError:
        raise json.JSONDecodeError


def str_to_date(string: str) -> datetime.date:
    # is this really necessary?
    # it is, what if the format changes
    return datetime.date.fromisoformat(string)


def get_week(in_date: datetime.date) -> int:
    return int(in_date.strftime("%W")) + (1 if datetime.date(in_date.year, 1, 1).weekday() != 0 else 0)


class FailedManager:
    def __init__(self, file_name: pathlib.Path or None = None) -> None:
        self.list = []
        self.file = open(file_name, mode="wt")

    def __del__(self) -> None:
        self.file.close()
        print(f"A total of {self.count} transfers has failed.", file=stderr)
        print("The paths to offending files " f"have benn written into {self.file.name}.", file=stderr)

    def handle_failure(self, file_name: pathlib.Path, reason: str) -> None:
        print(f"Transfer of {file_name.name} failed: {reason}\nAdding it to the list for manual review", file=stderr)
        self.list.append(file_name)
        self.file.write(str(file_name) + "\n")

    @property
    def count(self):
        return len(self.list)


# parse args and envvars
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

args = parser.parse_args(["-h"])
# add type hints
indir, outdir, failed, write = args.input, args.output, args.failed, args.write

try:
    if indir is None:
        indir = environ["SOURCE_DIRECTORY"]
    if outdir is None:
        outdir = environ["TARGET_DIRECTORY"]
except KeyError:
    print("Input or output missing!", file=stderr)
    exit(1)

# check perms on dirs (they might change, so we need to check again
# each time), nah, just check every time, assume nothing, this is the land of madness
# get files
fman = FailedManager(failed)
total_files = 0
for file in indir.glob("*.json"):
    total_files += 1
    with open(file, mode="r") as f:
        try:
            result = json.load(f, object_hook=as_entry)
        except json.JSONDecodeError:
            fman.handle_failure(file, "Malformed JSON")
            continue
        # check if dates match
        fname = file.parts[-1]
        fname_date = fname.split("_")[0]
        try:
            file_date = str_to_date(fname_date)
        except ValueError:
            file_date = None
        if file_date != result["date"]:
            # if not, store fname in review list and continue
            fman.handle_failure(file, "Date mismatch")
            continue
        # determine the year and week
        # the examples seem to suggest we want neither week 0 nor week 54
        # best to stick to iso 8601, even though some days will end up in the "wrong" year
        # eeeeeeh
        year, week = file_date.year, get_week(file_date)
        output_path = outdir / str(year) / str(week)
        outfile = output_path / "-".join(fname.split("-")[1:])
        info_dict = {
            "source": str(file),
            "target": str(outfile),
        }
        # print msg
        print(json.dumps(info_dict))
        if args.write:
            try:
                output_path.mkdir(exist_ok=True, parents=True)
                file.rename(output_path / fname)  # will not work across devices
            except OSError as e:
                fman.handle_failure(file, str(e))
        # if appropriate dir exists, move it there
        # otherwise attempt to create it, do not? fail critically

print(
    f"{'Success' if fman.count == 0 else 'Failure'}: processed {total_files - fman.count}/{total_files} files",
    file=stderr,
)
exit(fman.count)
