# Data

Raw, processed, and private data are not committed by default.

Expected layout:

```text
data/raw/        Downloaded or generated raw task data.
data/processed/  Derived public artifacts.
data/private/    Hidden labels and private temporal holdouts.
```

Each task must document data provenance and licensing in `docs/data_license_register.md`.

