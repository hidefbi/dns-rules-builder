# dns-rules-builder

Builds the signed DNS blocklist bundle used by **DNS Control**, a private fork of RethinkDNS
for Android. The bundle is published to `hidefbi/rules-old`, which the app downloads from
`https://hidefbi.github.io/rules-old/`.

## Repository layout

| Path | Purpose |
|---|---|
| `config.json` | The list configuration: 145 lists, with no `id` fields |
| `download.py` | Downloads every list in `config.json` |
| `src/build.js` | Builds the trie from the downloaded lists |
| `src/unames.json`, `src/log.js`, `src/ver.js` | Helpers used by `build.js` |
| `run_pack.sh` | Local download and build in one command |
| `ci_sign.py` | Writes the publish directory, `index.json`, signs and verifies it, writes `README.md` |
| `publish/README.head.md` | Static text at the top of the published `README.md` |
| `public.pem` | Public verification key. The private key is never stored in this repository |
| `.github/workflows/publish-rules.yml` | Build, report and publish workflow |

## List configuration

`config.json` has one object per list under `conf`:

```json
{
  "vname": "Example list",
  "group": "Privacy",
  "subg": "ExampleProject",
  "format": ["domains"],
  "url": ["https://example.org/list.txt"],
  "pack": ["liteprivacy"],
  "level": [0]
}
```

| Field | Type | Meaning |
|---|---|---|
| `vname` | string | Display name. Must be unique |
| `group` | string | One of `Privacy`, `Security`, `ParentalControl` |
| `subg` | string | Upstream project or author, for display and attribution |
| `format` | string or array | `domains`, `hosts`, `abp` or `wildcard`. One per URL, in order |
| `url` | string or array | Where the list is hosted |
| `pack` | array | Category tags, for example `adult`, `gambling`, `malware` |
| `level` | array | One severity per pack: `0` lite, `1` aggressive, `2` extreme |

Rules that must hold:

- Do not add an `id` field. List ids are positional: the first list is `0`, and so on up
  to `144`. The build fails if ids are not contiguous.
- Do not use `dead` or `ignore` as a pack. The build rejects them.
- Add new lists at the end of `conf`. Existing ids stay the same, so the app keeps its
  selections.
- Removing or reordering a list shifts the ids after it. Every user must then re-select
  their lists in the app after the update. Mention this in the release notes.

## Build locally

Requirements: Node.js 22, Python 3.12, `pip install aiohttp`, `npm ci --ignore-scripts`,
and about 14 GB of free RAM for the trie build.

```sh
HEAP=12288 ./run_pack.sh final config.json
```

This writes `files_final/` (downloaded lists) and `out_final/` (`td.txt`, `rd.txt`,
`basicconfig.json`, `filetag.json`). Both directories are ignored by git.

To produce a publish directory from a finished build (needs the private key):

```sh
SRC=out_final CFG=config.json KEY=/path/to/private.pem PUB=public.pem OUT=rules-publish python3 ci_sign.py
```

## Publishing

The workflow `publish-rules` has three entry points:

| Trigger | Builds | Publishes | Notes |
|---|---|---|---|
| Schedule (Monday 19:00 UTC, 15:00 GMT-4) | Yes | No | Opens a GitHub Issue with the change report |
| Manual, `confirm=DRY` | Yes | No | Use to test a change. The report is in the run log |
| Manual, `confirm=PUBLISH` and `source_run=<id>` | No | Yes | Publishes the artifact of a reviewed build |

Publishing from `source_run` does the following:

1. Downloads the artifact of that build and verifies the signature and every file hash.
2. Stops if the new version is not higher than the published one.
3. Requires approval of the `production` environment.
4. Replaces the content of `hidefbi/rules-old` with one commit.

Review the report before publishing. Check in particular the upstream URL changes.
A changed source URL is the most important thing to check.

## Secrets and environments

| Name | Where | Purpose |
|---|---|---|
| `PRIVATE_KEY` | Repository secret | ECDSA P-256 private key used to sign `index.json` |
| `RULES_TOKEN` | Repository secret | Fine-grained token with Contents read and write on `hidefbi/rules-old` only |
| `production` | Environment | Requires approval before publishing. Deployments are limited to `main` |

Never print a secret, paste it into an issue, commit it, or put it in a URL.
The private key must not be committed. Only `public.pem` belongs in the repository.

## Attribution and licensing

- The builder is derived from `serverless-dns/blocklists` by RethinkDNS and its authors,
  licensed under MPL-2.0. The modified source is in this repository.
- The trie engine `celzero/gotrie` is by RethinkDNS and its authors, licensed under MPL-2.0.
- DNS Control is a fork of RethinkDNS, licensed under Apache-2.0.
- Each list in `config.json` belongs to its upstream author and keeps that author's license.
  See the `url` field of each entry.

## Maintenance notes

- Upload to S3 or R2 is no longer used. Publication goes to `hidefbi/rules-old` only.
- The upstream `blocklist-builder` workflows (`publish-blocklists`, `MakeTrie`) are disabled
  and should be removed.
- Public repositories with no activity for 60 days have their scheduled workflows disabled.
  Keep the repository active, or re-enable the schedule manually.
