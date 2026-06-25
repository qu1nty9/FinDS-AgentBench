# Papers

Publication artifacts will be staged here:

- arXiv/workshop pilot paper;
- benchmark/dataset venue paper;
- journal extension;
- appendices and supplementary materials.

## Workshop Pilot

The reproducible arXiv/workshop manuscript scaffold is generated under
`papers/workshop_pilot/`:

```bash
PYTHONPATH=src python scripts/build_pilot_manuscript.py
```

The generated manuscript inputs release-owned LaTeX tables from
`docs/releases/pilot_v0/` so the paper remains tied to the canonical
benchmark snapshot instead of copying result tables by hand.

Run the static manuscript formatting check before PDF compilation:

```bash
PYTHONPATH=src python scripts/check_pilot_manuscript_formatting.py
```
