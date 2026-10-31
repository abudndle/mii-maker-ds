# Private BlocksDS Docker build (Nintendo DS / DSi)

This project contains **only source code**. A complete playable ROM must be
built using your own original-resource ZIP on your own computer.

## Requirements

- Docker Desktop (Windows/macOS) or Docker Engine (Linux).
- A checkout of `abudndle/mii-maker-ds` and the separately stored private
  `MiiMaker_DS_Resources.zip`.
- The official BlocksDS image: `skylyrac/blocksds:slim-latest`.
  See the [BlocksDS Docker documentation](https://blocksds.skylyrac.net/docs/setup/docker/).

## Private build

Open a terminal in the source-repository directory:

```sh
docker pull skylyrac/blocksds:slim-latest
python3 tools/build_private_docker.py /absolute/path/to/MiiMaker_DS_Resources.zip --validate-only
python3 tools/build_private_docker.py /absolute/path/to/MiiMaker_DS_Resources.zip --jobs 2
```

Windows examples use a local file such as
`C:\Users\You\Downloads\MiiMaker_DS_Resources.zip`; quote paths containing
spaces. The Python script handles Docker mount arguments without invoking a
shell. `--dry-run` previews those arguments, but it **does not validate or build**.

- The source directory is mounted at `/work`; the private ZIP is mounted
  **read-only** at `/private/resources.zip`. The container uses `--network none`,
  `--cap-drop ALL` and `no-new-privileges`; nothing uploads assets to GitHub.
- The project performs ZIP validation, original 53-clip motion checks, the
  327-clip GUI CLAN check (41 committed tracks), and all UI-art coverage checks
  **before extracting originals or compiling**.
- The private build then restores resources locally, compiles using BlocksDS,
  fixes DS/DSi ROM regions, and validates embedded assets, body models,
  ARM9/ARM7 sections and original motion clips.
- A successful real build writes `mii-ds.nds` into your local checkout.
  Do **not** publish that file: it contains privately supplied Nintendo data.
- Runtime fidelity and full feature parity still require testing in melonDS
  and on the intended DS/DSi hardware. A successful compile alone does not
  certify those behaviors.

## What GitHub CI checks (and what it does not)

The `BlocksDS ARM9 and ARM7 compile smoke` workflow uses the official
BlocksDS image to assemble an intentionally **nonplayable** synthetic ROM.
Its `nitrofiles/` entries and banner are entirely fictional placeholders.
The workflow checks that the C code cross-compiles, links and passes ROM
header/section validations; it deletes the resulting `.nds` and publishes
no ROM artifact. The job does not use your private archive and cannot
demonstrate faithful gameplay or original artwork.

If the official image isn't available on your computer, install BlocksDS
locally following its documentation and use
`python3 tools/build_private.py PRIVATE_ZIP` directly instead.
