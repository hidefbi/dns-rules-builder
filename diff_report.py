#!/usr/bin/env python3
"""Compare a fresh build with the currently published version.

Usage: python3 diff_report.py <build_out_dir> <published_blocklists_url>

Prints a Markdown report to stdout. The report compares per-list entry counts,
list membership and upstream URLs. It does not list individual domains, because
the published data does not include the upstream domain lists.
"""
import json
import os
import sys
import urllib.request

out_dir = sys.argv[1]
published_url = sys.argv[2]
update_url = published_url.rsplit('/', 1)[0] + '/update/blocklists'


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.load(resp)


new_ft = json.load(open(os.path.join(out_dir, 'filetag.json')))
new_bc = json.load(open(os.path.join(out_dir, 'basicconfig.json')))
new_ts = int(new_bc['timestamp'].split('/')[1])

notes = []
try:
    old_ft = fetch_json(published_url)
except Exception as e:  # first publish or network failure
    old_ft = {}
    notes.append('Could not read the published metadata (%s); every list is shown as new.' % e)
try:
    old_ts = fetch_json(update_url)['latest']
except Exception as e:
    old_ts = None
    notes.append('Could not read the published timestamp (%s).' % e)


def by_name(ft):
    return {v['vname']: v for v in ft.values()}


new = by_name(new_ft)
old = by_name(old_ft)
added = sorted(set(new) - set(old))
removed = sorted(set(old) - set(new))
common = sorted(set(new) & set(old))

url_changes = []
count_changes = []
for name in common:
    if old[name].get('url') != new[name].get('url'):
        url_changes.append(name)
    before = old[name].get('entries', 0)
    after = new[name].get('entries', 0)
    if before != after:
        count_changes.append((name, before, after, after - before))

total_old = sum(v.get('entries', 0) for v in old.values())
total_new = sum(v.get('entries', 0) for v in new.values())
delta = total_new - total_old
pct = (100.0 * delta / total_old) if total_old else 0.0

lines = []
lines.append('# Rules build report')
lines.append('')
for n in notes:
    lines.append('> ' + n)
if notes:
    lines.append('')
lines.append('| Item | Value |')
lines.append('|---|---|')
lines.append('| New build timestamp | `%d` |' % new_ts)
lines.append('| Published timestamp | `%s` |' % (old_ts if old_ts is not None else 'unknown'))
lines.append('| Lists (new / published) | %d / %d |' % (len(new), len(old)))
lines.append('| Domain entries (new / published) | %d / %d |' % (total_new, total_old))
lines.append('| Change in entries | %+d (%+.2f%%) |' % (delta, pct))
lines.append('')

lines.append('## Lists added (%d)' % len(added))
if added:
    lines.extend('- ' + n for n in added)
else:
    lines.append('None.')
lines.append('')
lines.append('## Lists removed (%d)' % len(removed))
if removed:
    lines.extend('- ' + n for n in removed)
else:
    lines.append('None.')
lines.append('')

lines.append('## Upstream URL changes (%d)' % len(url_changes))
lines.append('Review these before publishing. A changed source URL is the most important thing to check.')
if url_changes:
    lines.extend('- ' + n for n in url_changes)
else:
    lines.append('None.')
lines.append('')

count_changes.sort(key=lambda r: -abs(r[3]))
lines.append('## Entry count changes (%d lists, largest first, top 40 shown)' % len(count_changes))
lines.append('| List | Before | After | Change |')
lines.append('|---|---:|---:|---:|')
for name, before, after, change in count_changes[:40]:
    lines.append('| %s | %d | %d | %+d |' % (name, before, after, change))
if not count_changes:
    lines.append('| (no changes) | | | |')
lines.append('')
print('\n'.join(lines))
