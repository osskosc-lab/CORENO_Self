# Repository Architecture

```text
CORENO_Self/
├── README.md
├── requirements.txt
├── docs/
│   ├── RESEARCH_STATUS.md
│   ├── DECISION_POLICY.md
│   └── REPOSITORY_ARCHITECTURE.md
├── paper/
│   └── README.md
├── phase0a/
│   ├── README.md
│   ├── spec/
│   │   └── CORENO_Self_Phase0A_v1_1_Spec_Amendment.md
│   ├── work/
│   │   └── CORENO_Self_Phase0A_v1_1_Work_Prompt.json
│   └── src/
│       └── coreno_self_phase0a_v1_1.py
└── .github/workflows/
    ├── phase0a-smoke.yml
    └── phase0a-frozen-qual.yml
```

## Separation of concerns

- `paper/`: conceptual source and publication freeze
- `phase0a/spec/`: frozen methodological amendments
- `phase0a/work/`: Work execution contract
- `phase0a/src/`: executable frozen qualification
- `docs/`: status and governance rules
- GitHub Actions artifacts: generated evidence; generated results are not silently committed

## Branch policy

Research changes should be introduced on feature branches and reviewed before merge. Frozen QUAL should be launched from a reviewed commit and its source SHA recorded with the artifact.

## Next phase boundary

Phase 0B is not authorized merely because the code runs. It becomes the next candidate only if the frozen Phase 0A verdict is `SYNTHETIC_QUAL_PASS`. Its narrow purpose should be non-oracle `U_hat` estimation while keeping Phase 0A gates frozen.
