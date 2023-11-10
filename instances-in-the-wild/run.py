#!/usr/bin/python3

import argparse
import logging
import os
import random
import re
import subprocess
import sys
import urllib.request
import yaml

from datetime import datetime

from bs4 import BeautifulSoup

OUTDIR = ""


def parse_last_updated(text):
    # Return how many days the mirror is outdated
    m = re.match(r"(\d+) years? ago", text)
    if m:
        return int(m.group(1)) * 365
    m = re.match(r"(\d+) days? ago", text)
    if m:
        return int(m.group(1))
    return 0


def parse_footer(text):
    # Return mirrorbits version
    m = re.match(r"Mirrorbits (\S+) running on ", text)
    if m:
        return m.group(1)
    return None


def do_mirrorstats(instance, url):

    log.info("Requesting %s ...", url)

    version = None
    mirrors = []

    # Get the page
    try:
        with urllib.request.urlopen(url) as f:
            html = f.read()
    except urllib.error.URLError as e:
        log.error("URLError: %s", e)
        return version, mirrors

    # Parse the page
    html = BeautifulSoup(html, features="lxml")

    # Get mirrorbits version
    div = html.body.find("div", attrs={"id": "footer"})
    if not div:
        log.error("Couldn't find <div id=\"footer\"> in HTML")
    else:
        footer = div.text.strip()
        version = parse_footer(footer)
        log.debug(footer)

    # Get the list of mirrors
    div = html.body.find("div", attrs={"id": "chart"})
    if not div:
        log.error("Couldn't find <div id=\"chart\"> in HTML")
    else:
        rows = div.find_all("tr")
        rows = rows[1:]  # remove table header
        for idx, row in enumerate(rows):
            # each mirror takes two rows
            if idx % 2 != 0:
                continue
            cells = row.find_all("td")
            mirror = cells[0].text
            last_updated = cells[2].text
            outdated = parse_last_updated(last_updated)
            item = {
                "name": mirror,
                "outdated": outdated,
            }
            mirrors.append(item)
            log.debug("%s", item)

    # Sort mirrors per name
    mirrors = sorted(mirrors, key=lambda d: d["name"])

    # Save output
    if OUTDIR:
        if not os.path.isdir(OUTDIR):
            os.mkdir(OUTDIR)

        with open(f"{OUTDIR}/{instance}.version", "w") as f:
            f.write(version or "unknown")
            f.write("\n")

        with open(f"{OUTDIR}/{instance}.mirrors", "w") as f:
            f.write("# mirror days-outdated\n")
            for item in mirrors:
                f.write(f"{item['name']} {item['outdated']}\n")

    return mirrors, version


def do_rsync(instance, url):

    log.info("Requesting %s ...", url)

    # Run the rsync command
    cmd = ["rsync", "-r", "--no-motd", "--timeout=30",
           "--contimeout=30", "--exclude=.~tmp~/", url]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        log.error("Command failed: %s", cmd)
        if p.stderr:
            log.error("%s", p.stderr)
        return 0

    # Count files
    n_files = 0
    for line in p.stdout.splitlines():
        if line.startswith("-"):
            n_files += 1

    # Save output
    if OUTDIR:
        if not os.path.isdir(OUTDIR):
            os.mkdir(OUTDIR)

        with open(f"{OUTDIR}/{instance}.rsync", "w") as f:
            f.write(p.stdout)

    return n_files


def process_instance(instance, data):
    log.info(">>> Processing %s", instance)

    # Get and process mirrorstats
    mirrors = []
    version = None
    if True:
        url = data['mirrorstats']
        mirrors, version = do_mirrorstats(instance, url)
        print(f"Mirrorbits version: {version or 'unknown'}")
        print(f"Number of mirrors : {len(mirrors)}")

    # Get and process mirrorlist - NOT IMPLEMENTED!
    if False:
        url = data['mirrorlist']
        mirrors, version = do_mirrorlist(instance, url)
        # todo: https/http variant

    # List files on the mirror via rsync
    n_files = 0
    if True:
        urls = data['rsync']
        random.shuffle(urls)
        for url in urls:
            n_files = do_rsync(instance, url)
            if n_files != 0:
                break
        print(f"Number of files: {n_files}")

    return {
        "version": version,
        "mirrors": mirrors,
        "n_files": n_files,
    }


def print_markdown(all_data):

    with_links = True

    print()

    if with_links:
        print(f"| Instance                   | Since           | Prod | Pkgs?    | Mir | Act | Files | Version                  |")
        print(f"| -------------------------- | --------------: | ---- | -------- | --: | --: | ----: | ------------------------ |")
    else:
        print(f"| Instance            | Since    | Prod | Pkgs?    | Mir | Act | Files | Version                  |")
        print(f"| ------------------- | -------: | ---- | -------- | --: | --: | ----: | ------------------------ |")

    count = 0
    for inst, data in all_data.items():

        name = data.get("name", inst.capitalize())
        since = data.get("since", None)

        if since:
            # pretty, but doesn't sort
            #since = since["date"].strftime("%B %Y")
            since = since["date"].strftime("%Y-%m")
        else:
            since = "unknown"

        prod = "✓" if data["prod"] else "✗"
        pkgs = ", ".join(data.get("pkgs", []))

        out = data["output"]
        version = out["version"] or "unknown"
        mirrors = out["mirrors"]

        n_mirrors = len(mirrors)

        active_mirrors = 0
        for item in mirrors:
            if item['outdated'] < 30:
                active_mirrors += 1

        n_files = out["n_files"]

        if n_files > 1000:
            n_files = round(n_files / 1000)
            n_files = f"{n_files}k"

        if with_links:
            name = f"[{name}][{count:02}a]"
            if since != "unknown":
                since = f"[{since}][{count:02}b]"
            print(f"| {name:<26} | {since:>16} | {prod:<4} | {pkgs:<9} | {n_mirrors:>3} | {active_mirrors:>3} | {n_files:>5} | {version:<24} |")
        else:
            print(f"| {name:<19} | {since:>9} | {prod:<4} | {pkgs:<9} | {n_mirrors:>3} | {active_mirrors:>3} | {n_files:>5} | {version:<24} |")

        count += 1

    # Add the links
    if with_links:
        print()
        count = 0
        for inst, data in all_data.items():
            print(f"[{count:02}a]: {data['homepage']}")
            if "since" in data:
                print(f"[{count:02}b]: {data['since']['url']}")
            count += 1


# main


parser = argparse.ArgumentParser(description="Details on mirrorbits instances in the wild")
parser.add_argument("-d", "--debug", action="store_true",
    help="print debug messages")
parser.add_argument("-i", "--instance",
    help="process only a particular instance")
parser.add_argument("-o", "--outdir",
    help="dump a lot of data into outdir")
parser.add_argument("YAML_FILE")
args = parser.parse_args()

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG if args.debug else logging.INFO)

OUTDIR = args.outdir

with open(args.YAML_FILE, "r") as f:
    yaml_data = yaml.safe_load(f)

new_data = {}
for inst, data in yaml_data.items():
    # Might want to skip
    if args.instance and inst != args.instance:
        continue

    # Process
    result = process_instance(inst, data)
    new_data[inst] = data
    new_data[inst]["output"] = result

print_markdown(new_data)
