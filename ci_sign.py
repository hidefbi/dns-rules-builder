#!/usr/bin/env python3
# Build the publish directory from a finished build: copy files, write the
# update manifest, index.json (with sha256 and size of every file), sign it
# with ECDSA P-256 / SHA-256 and verify the signature.
#
# Environment variables:
#   SRC   build output directory (default: ./out)
#   CFG   list configuration used for the build (default: ./config.json)
#   KEY   path to the PEM private key (required)
#   PUB   path to the PEM public key (default: ./public.pem)
#   OUT   publish directory to create (default: ./rules-publish)
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('SRC', os.path.join(ROOT, 'out'))
CFG = os.environ.get('CFG', os.path.join(ROOT, 'config.json'))
KEY = os.environ['KEY']
PUB = os.environ.get('PUB', os.path.join(ROOT, 'public.pem'))
OUT = os.environ.get('OUT', os.path.join(ROOT, 'rules-publish'))


def p(name):
    return os.path.join(OUT, name)


def file_hash(path, algo):
    h = hashlib.new(algo)
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(os.path.join(OUT, 'update'))

bc = json.load(open(os.path.join(SRC, 'basicconfig.json')))
ts = int(bc['timestamp'].split('/')[1])

# (source file in SRC, published name)
PAIRS = [
    ('filetag.json', 'blocklists'),
    ('basicconfig.json', 'basicconfig'),
    ('rd.txt', 'rank'),
    ('td.txt', 'trie'),
]
for src_name, dst_name in PAIRS:
    shutil.copyfile(os.path.join(SRC, src_name), p(dst_name))

# The build reports its own checksums; they must match the copied files.
assert file_hash(p('trie'), 'md5') == bc['tdmd5'], 'trie md5 mismatch'
assert file_hash(p('rank'), 'md5') == bc['rdmd5'], 'rank md5 mismatch'
assert file_hash(p('blocklists'), 'md5') == bc['ftmd5'], 'blocklists md5 mismatch'

with open(p('update/blocklists'), 'w') as f:
    f.write(json.dumps({'version': 1, 'update': True, 'latest': ts}) + '\n')
open(p('.nojekyll'), 'w').close()

ft = json.load(open(os.path.join(SRC, 'filetag.json')))
sources = []
for v in ft.values():
    urls = v['url'] if isinstance(v['url'], list) else [v['url']]
    sources.append({'name': v['vname'], 'entries': v.get('entries', 0), 'url': urls})

manifest = {
    'files': {
        dst: {'sha256': file_hash(p(dst), 'sha256'), 'size': os.path.getsize(p(dst))}
        for _, dst in PAIRS
    },
    'generated_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'schema_version': 1,
    'sequence': ts,
    'sources': sources,
}
with open(p('index.json'), 'w') as f:
    f.write(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + '\n')

# Sign index.json. The .sig file is the base64 of the DER signature.
sig = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', KEY, p('index.json')],
                     capture_output=True, check=True).stdout
b64 = subprocess.run(['openssl', 'base64', '-A'], input=sig,
                     capture_output=True, check=True).stdout
with open(p('index.json.sig'), 'wb') as f:
    f.write(b64)

# Verify the signature with the public key before anything is published.
with tempfile.TemporaryDirectory() as tmp:
    sig_der = os.path.join(tmp, 'sig.der')
    with open(sig_der, 'wb') as f:
        f.write(sig)
    result = subprocess.run(
        ['openssl', 'dgst', '-sha256', '-verify', PUB, '-signature', sig_der, p('index.json')],
        capture_output=True, text=True)
print('signature check:', result.stdout.strip(), result.stderr.strip())
assert result.returncode == 0 and 'Verified OK' in result.stdout, 'signature verification failed'

# README listing every list and its upstream source.
conf = json.load(open(CFG))['conf']
lines = [
    '# dns-rules',
    '',
    'Personal build of public DNS blocklists, compiled with the MPL-2.0 '
    'serverless-dns/blocklists builder.',
    'Every list belongs to its original authors and keeps its own license; '
    'see the upstream URL.',
    '',
    '| List | Group | Upstream |',
    '|---|---|---|',
]
for e in conf:
    urls = e['url'] if isinstance(e['url'], list) else [e['url']]
    lines.append('| %s | %s | %s |' % (e['vname'], e.get('group', ''), '<br>'.join(urls)))
with open(p('README.md'), 'w') as f:
    f.write('\n'.join(lines) + '\n')

print('sequence/latest =', ts)
