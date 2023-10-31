#!/usr/bin/python3

import json
import logging
import os
import sys

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

if sys.argv[1] in ["-d", "--debug"]:
    log.setLevel(logging.DEBUG)
    sys.argv.pop(1)

DATADIR = sys.argv[1]
DATAFILES = sorted(os.listdir(DATADIR))

for fn in DATAFILES:
    if fn.endswith(".swp"):
        continue

    if not fn.endswith(".json"):
        log.info("Skipping %s (not a .json)", fn)
        continue

    date = os.path.splitext(fn)[0]

    fn = os.path.join(DATADIR, fn)

    if os.stat(fn).st_size == 0:
        log.info("Skipping %s (empty)", fn)
        continue

    log.debug("Doing %s", fn)

    with open(fn) as f:
        data = json.load(f)

    mirrorlist = data['MirrorList']
    excludedlist = data.get('ExcludedList', [])

    n_included = len(mirrorlist)
    n_excluded = len(excludedlist)
    n_total = n_included + n_excluded

    # reasons why the mirror was excluded
    country_only = 0
    file_not_found = 0
    file_size_mismatch = 0
    mod_time_mismatch = 0
    other_reason = 0
    unreachable = 0

    for m in excludedlist:
        reason = m['ExcludeReason']
        if "Country only" in reason:
            country_only += 1
        elif "File not found" in reason:
            file_not_found += 1
        elif "File size mismatch" in reason:
            file_size_mismatch += 1
        elif "Mod time mismatch" in reason:
            mod_time_mismatch += 1
        elif "Unreachable" in reason:
            unreachable += 1
        else:
            other_reason += 1

    fallback = data.get('Fallback', False)
    fallback = 1 if fallback else 0

    print(f"{date} {n_total} {n_included} {n_excluded} {country_only} {file_not_found} {file_size_mismatch} {mod_time_mismatch} {unreachable} {other_reason} {fallback}")
