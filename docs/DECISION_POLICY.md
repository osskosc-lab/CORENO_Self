# Decision Policy

CORENO Self uses a falsification-first decision policy. A result is not forced into PASS/FAIL when the evidence only supports uncertainty.

## Component labels

For relative degradation

```text
r = (L_reduced - L_full) / L_full
```

the Phase 0A v1.1 frozen rules are:

- **SUPPORTED_COMPONENT** — bootstrap 95% lower confidence bound > +0.05
- **PRACTICALLY_EQUIVALENT** — the full 95% CI lies within [-0.02, +0.02]
- **INCONCLUSIVE** — neither rule is met

An `INCONCLUSIVE` result does **not** authorize theory reduction.

## Overall labels

- **SYNTHETIC_QUAL_PASS**
- **COMPONENT_EQUIVALENCE_REDUCE_THEORY**
- **INCONCLUSIVE_COMPONENT_NECESSITY**
- **QUAL_FAIL**

## Negative controls have priority

A failure of the STATE_SUFFICIENT equivalence control, carrier-erasure control, or identity operationalization invalidates a positive-looking component result for the frozen qualification.

## Non-gating diagnostics

The original M0–M3 information ladder and oracle-U removal are reported but do not serve as structural evidence in Phase 0A v1.1.

## Post-hoc policy

Do not change seeds, generator parameters, thresholds, estimators, equivalence margins, or bootstrap counts after seeing frozen-run results. A code bug may be fixed only with an explicit before/after source hash and audit note.
