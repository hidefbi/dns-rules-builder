# dns-rules-builder

Builds the DNS blocklist bundle consumed by the DNS Control app.
Output is published to https://github.com/hidefbi/rules-old.

## Layout

- config.json: 145 lists. Ids are positional (0..144); do not add id fields.
- download.py: downloads every list.
- src/: trie builder (build.js) and its helpers.
- ci_sign.py: writes the publish directory and index.json, then signs it (ECDSA P-256 / SHA-256).
- run_pack.sh: local download and build.
- public.pem: public verification key. The private key is never stored in this repository.
- .github/workflows/publish-rules.yml: manual build; publishing requires approval.

## Local build

    HEAP=12288 ./run_pack.sh final config.json

## Publish

Run the publish-rules workflow manually. The build runs first. Publishing runs only when
the input confirm is PUBLISH and the production environment is approved.

## Secrets

- PRIVATE_KEY: signing key (PEM).
- RULES_TOKEN: fine-grained token, hidefbi/rules-old only, Contents: read and write.
