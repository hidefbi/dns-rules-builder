# DNS Control rules

Signed blocklist data for **DNS Control**, a private fork of RethinkDNS for Android.
The app downloads this data over HTTPS from `https://hidefbi.github.io/rules-old/`.

This repository is a release artifact only. It contains no source code.
The build tooling is maintained in `hidefbi/dns-rules-builder`.

## Contents

| File | Description |
|---|---|
| `trie` | Compiled domain trie read by the app's DNS engine (binary) |
| `rank` | Rank directory for `trie` (binary) |
| `basicconfig` | Build metadata: codec, build timestamp, checksums |
| `blocklists` | List metadata: numeric id, name, group, upstream URLs |
| `index.json` | Release manifest: sequence number, sha256 and size of each data file, sources |
| `index.json.sig` | Base64-encoded DER signature of `index.json` (ECDSA P-256, SHA-256) |
| `update/blocklists` | Latest version number. The app checks this before downloading |
| `public.pem` | Public key that verifies `index.json.sig` |
| `README.md` | This document |

## Verifying a release

1. Download `index.json` and `index.json.sig`.
2. Decode the signature:

   ```sh
   base64 -d index.json.sig > sig.der
   ```

3. Verify it with the public key in this repository:

   ```sh
   openssl dgst -sha256 -verify public.pem -signature sig.der index.json
   ```

   The output must be `Verified OK`.

4. For each entry under `files` in `index.json`, check that the downloaded file matches
   its `sha256` and `size`.

## Versioning

- A version is a Unix timestamp in milliseconds. The value in `update/blocklists` (`latest`)
  is the same as `sequence` in `index.json`.
- Each release has a higher version than the one before it. The app rejects any
  release whose version is lower than the last one it installed.
- Each release replaces the repository history with a single commit. Identify a release
  by its `index.json`, not by its commit.

## Release process

- Releases are built from a fixed configuration of 145 lists.
- Each build is checked for the list count, contiguous list ids, empty lists and checksums,
  then signed and verified.
- A release is published by hand after its build report is reviewed. Nothing is published
  automatically.
- A weekly build runs on a schedule and never publishes. It opens a report for review.

## Licensing and sources

- The build tooling is licensed under the Mozilla Public License 2.0 (MPL-2.0).
- The lists are third-party data. Each list keeps its own license and is listed with its
  upstream URL in the table below. This repository redistributes them only in compiled form,
  for personal use. Check each source's terms before reusing the data.
- The data is provided as is, without warranty of any kind.

## Attribution

- **RethinkDNS and its authors** (https://github.com/celzero) created the software this
  data is built with:
  - the blocklist builder, derived from `serverless-dns/blocklists` (MPL-2.0);
  - the `gotrie` trie engine (MPL-2.0), which reads these files;
  - RethinkDNS, the upstream project for the DNS Control app, licensed under Apache-2.0.
- **Upstream list authors** maintain the blocklists in the table below. Their names and
  licenses are on their own pages, and the credit for the underlying data belongs to them.
- The build configuration, release process and this document are maintained by the
  publisher of this repository (`hidefbi`).

## Reporting problems

Open an issue in this repository. Include the list name and the domain involved.

