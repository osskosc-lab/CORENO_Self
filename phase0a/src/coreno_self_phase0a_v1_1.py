#!/usr/bin/env python3
"""CORENO Self Phase 0A v1.1 — Minimal Synthetic Qualification.

This is a falsification-first SYNTHETIC qualification script.
It does not validate human selfhood, consciousness, qualia, soul, or ontology.

v1.1 fixes six audit issues:
1) Oracle U advantage is reported only as an information-set diagnostic, not as
   architectural evidence.
2) STATE_SUFFICIENT is tested by a pre-frozen practical-equivalence margin.
3) Boundary/access/history necessity is tested with RETRAINED reduced models.
4) History causal audit permutes event order BEFORE carrier regeneration.
5) Access is handled coherently through paired access-specific observations,
   boundaries and targets; no label-only swap is used.
6) All uncertainty is bootstrapped at the SEED level with pairing preserved.

Identity audit also operationalizes BOTH d_F and C(Gamma1,Gamma2), including a
long-horizon rollout distance and a known-lineage continuity score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class FrozenConfig:
    n_seeds: int = 64
    n_trajectories: int = 48
    steps_per_trajectory: int = 64
    train_fraction: float = 0.70
    ridge_alpha: float = 1.0
    bootstrap_reps: int = 20000
    bootstrap_seed: int = 90210

    # Evidence margins (all frozen before the run)
    component_support_margin: float = 0.05   # >=5% relative degradation
    component_equiv_margin: float = 0.02     # practical equivalence +/-2%
    null_equiv_margin: float = 0.02          # STATE_SUFFICIENT +/-2%
    history_causal_min_effect: float = 0.05  # absolute paired response effect
    history_erased_max_effect: float = 0.01

    # Identity audit; F outputs are frozen to [-1, 1]
    epsilon_F_short: float = 0.10
    epsilon_F_long: float = 0.15
    tau_C: float = 0.80
    df_probe_n: int = 4096
    df_horizon: int = 32

    full_seed_start: int = 11000
    null_seed_start: int = 21000
    history_seed_start: int = 31000

    # Synthetic dynamics
    x_noise: float = 0.20
    obs_noise: float = 0.12
    history_noise: float = 0.08
    y_noise: float = 0.20
    history_decay: float = 0.78
    boundary_decay: float = 0.58


# Original paper ladder: informative only, NOT architectural evidence because M3 has oracle U.
INFO_FEATURES = {
    "M0": ["S0", "S1", "S2"],
    "M1": ["S0", "S1", "S2", "H0", "H1"],
    "M2": ["B", "H0", "H1"],
    "M3": ["B", "H0", "H1", "U0", "U1", "A"],
}

# Matched-information structural family. Every comparison is retrained from scratch.
STRUCT_FEATURES = {
    "FULL": ["S0", "S1", "S2", "B", "H0", "H1", "U0", "U1", "A"],
    "NO_B": ["S0", "S1", "S2", "H0", "H1", "U0", "U1", "A"],
    "NO_H": ["S0", "S1", "S2", "B", "U0", "U1", "A"],
    "NO_A": ["S0", "S1", "S2", "B", "H0", "H1", "U0", "U1"],
    "NO_U": ["S0", "S1", "S2", "B", "H0", "H1", "A"],
}

# Negative-control family. In STATE_SUFFICIENT, S alone is sufficient.
NULL_FEATURES = {
    "BASE_S": ["S0", "S1", "S2"],
    "FULL_EXTRA": ["S0", "S1", "S2", "B", "H0", "H1", "U0", "U1", "A"],
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_matrix() -> np.ndarray:
    return np.array([
        [0.63, 0.10, 0.00, 0.05, 0.00],
        [0.04, 0.60, 0.10, 0.00, 0.05],
        [0.00, 0.06, 0.58, 0.08, 0.00],
        [0.03, 0.00, 0.04, 0.55, 0.12],
        [0.00, 0.04, 0.00, 0.08, 0.57],
    ], dtype=float)


def access_observation(x: np.ndarray, access: int, rng: np.random.Generator, noise: float) -> np.ndarray:
    if access == 0:
        base = np.array([
            x[0] + 0.20*x[3],
            x[1] + 0.10*x[4],
            x[2] - 0.10*x[3],
        ])
    else:
        base = np.array([
            x[0] - 0.15*x[4],
            x[1] + 0.20*x[3],
            x[2] + 0.25*x[4],
        ])
    return base + rng.normal(0, noise, size=3)


def boundary_value(prev_b: float, s: np.ndarray, h: np.ndarray, u: np.ndarray,
                   access: int, cfg: FrozenConfig) -> float:
    # Deterministic given current variables in v1.1: avoids hidden extra boundary noise.
    return float(np.tanh(
        cfg.boundary_decay*prev_b
        + 0.24*s[0] - 0.18*s[1] + 0.08*s[2]
        + 0.30*h[0] - 0.24*h[1]
        + 0.28*u[0] - 0.20*u[1]
        + 0.18*(2*access - 1)
    ))


def response_value(s: np.ndarray, b: float, h: np.ndarray, u: np.ndarray,
                   access: int, noise: float, regime: str) -> float:
    if regime == "FULL":
        return float(
            0.55*s[0] - 0.34*s[1] + 0.20*s[2]
            + 0.46*b
            + 0.34*h[0] - 0.28*h[1]
            + 0.38*u[0] - 0.31*u[1]
            + 0.24*(2*access - 1)
            + noise
        )
    if regime == "STATE_SUFFICIENT":
        return float(0.95*s[0] - 0.72*s[1] + 0.54*s[2] + noise)
    raise ValueError(regime)


def generate_dataset(seed: int, cfg: FrozenConfig, regime: str) -> pd.DataFrame:
    """Generate coherent access twins from the same underlying state.

    Each latent time point produces access=0 and access=1 rows. Observation S,
    boundary B, and target Y are recomputed coherently for each access. No label-only
    swapping is used anywhere in this script.
    """
    rng = np.random.default_rng(seed)
    A_dyn = stable_matrix()
    rows: List[Dict[str, float]] = []

    for traj in range(cfg.n_trajectories):
        x = rng.normal(0, 0.25, size=5)
        h = rng.normal(0, 0.10, size=2)
        b_prev = {0: 0.0, 1: 0.0}
        phase = rng.uniform(0, 2*np.pi)

        for t in range(cfg.steps_per_trajectory):
            env = np.sin(2*np.pi*t/19.0 + phase) + 0.35*np.cos(2*np.pi*t/31.0)
            exo = np.array([0.20, -0.10, 0.15, 0.10, -0.08]) * env
            x = A_dyn @ x + exo + rng.normal(0, cfg.x_noise, size=5)
            u = np.array([x[3], x[4]], dtype=float)  # ORACLE latent, synthetic only

            # Shared response noise across access twins to isolate coherent access change.
            pair_noise = float(rng.normal(0, cfg.y_noise))
            pair_id = traj * cfg.steps_per_trajectory + t

            for access in (0, 1):
                # independent observation noise is part of each access operator
                s = access_observation(x, access, rng, cfg.obs_noise)
                b = boundary_value(b_prev[access], s, h, u, access, cfg)
                y = response_value(s, b, h, u, access, pair_noise, regime)
                rows.append({
                    "seed": seed, "traj": traj, "t": t, "pair_id": pair_id,
                    "S0": float(s[0]), "S1": float(s[1]), "S2": float(s[2]),
                    "H0": float(h[0]), "H1": float(h[1]),
                    "B": float(b), "U0": float(u[0]), "U1": float(u[1]),
                    "A": float(2*access - 1), "Y": float(y),
                })
                b_prev[access] = b

            # Update history carrier after both access twins are recorded.
            h = (
                cfg.history_decay*h
                + np.array([0.42*x[0] + 0.15*x[3], -0.30*x[1] + 0.18*x[4]])
                + rng.normal(0, cfg.history_noise, size=2)
            )

    return pd.DataFrame(rows)


def split_by_trajectory(df: pd.DataFrame, train_fraction: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    trajs = np.sort(df["traj"].unique())
    n_train = max(1, int(len(trajs) * train_fraction))
    train_ids = set(trajs[:n_train].tolist())
    train = df[df["traj"].isin(train_ids)].copy()
    test = df[~df["traj"].isin(train_ids)].copy()
    return train, test


def make_model(alpha: float) -> Pipeline:
    return Pipeline([
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=alpha)),
    ])


def fit_mse(train: pd.DataFrame, test: pd.DataFrame, features: List[str], alpha: float) -> Tuple[float, Pipeline]:
    model = make_model(alpha)
    model.fit(train[features].to_numpy(), train["Y"].to_numpy())
    pred = model.predict(test[features].to_numpy())
    return float(mean_squared_error(test["Y"].to_numpy(), pred)), model


def evaluate_seed(seed: int, cfg: FrozenConfig, regime: str) -> Dict[str, float]:
    df = generate_dataset(seed, cfg, regime)
    train, test = split_by_trajectory(df, cfg.train_fraction)
    out: Dict[str, float] = {"seed": seed}

    # Original paper ladder: report only.
    for name, feat in INFO_FEATURES.items():
        mse, _ = fit_mse(train, test, feat, cfg.ridge_alpha)
        out[f"info_mse_{name}"] = mse

    # Structural retraining family.
    for name, feat in STRUCT_FEATURES.items():
        mse, _ = fit_mse(train, test, feat, cfg.ridge_alpha)
        out[f"struct_mse_{name}"] = mse

    # Negative-control family.
    for name, feat in NULL_FEATURES.items():
        mse, _ = fit_mse(train, test, feat, cfg.ridge_alpha)
        out[f"null_mse_{name}"] = mse

    # Coherent access-twin target difference (descriptive DGP audit, not label swap).
    piv = test.pivot(index="pair_id", columns="A", values="Y").dropna()
    if (-1.0 in piv.columns) and (1.0 in piv.columns):
        out["coherent_access_target_absdiff"] = float(np.mean(np.abs(piv[1.0] - piv[-1.0])))
    else:
        out["coherent_access_target_absdiff"] = np.nan

    return out


def history_carrier_from_events(events: np.ndarray, order: np.ndarray, decay: float) -> np.ndarray:
    h = np.zeros(2, dtype=float)
    W = np.array([[0.55, -0.20], [0.15, 0.45]])
    for idx in order:
        h = decay*h + W @ events[idx]
    return h


def history_order_audit(seed: int, cfg: FrozenConfig, n_pairs: int = 512) -> Dict[str, float]:
    """Causal synthetic audit: reorder events BEFORE regenerating H.

    Same multiset of events, different order. Current S/U/A are matched. The carrier H
    is regenerated from the reordered sequence, then B and Y are recomputed with shared
    response noise. A second erased-carrier control sets H=0 in both conditions.
    """
    rng = np.random.default_rng(seed)
    diffs = []
    erased_diffs = []

    order_a = np.array([0, 1, 2, 3])
    order_b = np.array([3, 1, 0, 2])

    for _ in range(n_pairs):
        events = rng.normal(0, 1, size=(4, 2))
        h_a = history_carrier_from_events(events, order_a, cfg.history_decay)
        h_b = history_carrier_from_events(events, order_b, cfg.history_decay)

        s = rng.normal(0, 0.7, size=3)
        u = rng.normal(0, 0.5, size=2)
        access = int(rng.integers(0, 2))
        common_noise = float(rng.normal(0, cfg.y_noise))

        b_a = boundary_value(0.0, s, h_a, u, access, cfg)
        b_b = boundary_value(0.0, s, h_b, u, access, cfg)
        y_a = response_value(s, b_a, h_a, u, access, common_noise, "FULL")
        y_b = response_value(s, b_b, h_b, u, access, common_noise, "FULL")
        diffs.append(abs(y_a - y_b))

        h0 = np.zeros(2)
        b0a = boundary_value(0.0, s, h0, u, access, cfg)
        b0b = boundary_value(0.0, s, h0, u, access, cfg)
        y0a = response_value(s, b0a, h0, u, access, common_noise, "FULL")
        y0b = response_value(s, b0b, h0, u, access, common_noise, "FULL")
        erased_diffs.append(abs(y0a - y0b))

    return {
        "seed": seed,
        "history_order_abs_effect": float(np.mean(diffs)),
        "history_erased_abs_effect": float(np.mean(erased_diffs)),
    }


def seed_boot_ci(values: np.ndarray, reps: int, rng: np.random.Generator) -> Tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    n = len(values)
    idx = rng.integers(0, n, size=(reps, n))
    boot = values[idx].mean(axis=1)
    return float(values.mean()), float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))


def seed_boot_ratio(num: np.ndarray, den: np.ndarray, reps: int, rng: np.random.Generator) -> Tuple[float, float, float]:
    num = np.asarray(num, dtype=float)
    den = np.asarray(den, dtype=float)
    n = len(num)
    idx = rng.integers(0, n, size=(reps, n))
    boot = num[idx].mean(axis=1) / den[idx].mean(axis=1)
    point = float(num.mean() / den.mean())
    return point, float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))


def classify_component(rel_deg_ci: Tuple[float, float, float], cfg: FrozenConfig) -> str:
    point, lo, hi = rel_deg_ci
    if lo > cfg.component_support_margin:
        return "SUPPORTED_COMPONENT"
    if lo >= -cfg.component_equiv_margin and hi <= cfg.component_equiv_margin:
        return "PRACTICALLY_EQUIVALENT"
    return "INCONCLUSIVE"


def update_step(state: float, exo5: np.ndarray, theta: np.ndarray) -> float:
    z = np.concatenate([[state], exo5])
    return float(np.tanh(z @ theta))  # fixed output scale [-1,1]


def rollout(initial: float, exo_seq: np.ndarray, theta: np.ndarray) -> np.ndarray:
    s = float(initial)
    out = []
    for exo in exo_seq:
        s = update_step(s, exo, theta)
        out.append(s)
    return np.asarray(out)


def continuity_score(lineage_known: bool, end_state_1: float, start_state_2: float,
                     end_h_1: np.ndarray, start_h_2: np.ndarray,
                     end_b_1: float, start_b_2: float) -> float:
    # C includes causal lineage explicitly; an independent same-rule clone cannot pass.
    if not lineage_known:
        return 0.0
    c_state = np.exp(-abs(start_state_2 - end_state_1) / 0.10)
    c_hist = np.exp(-np.linalg.norm(start_h_2 - end_h_1) / 0.20)
    c_bound = np.exp(-abs(start_b_2 - end_b_1) / 0.10)
    c_viability = 1.0 if (abs(end_state_1) <= 1 and abs(start_state_2) <= 1) else 0.0
    return float(np.mean([c_state, c_hist, c_bound, c_viability]))


def identity_audit(cfg: FrozenConfig) -> Dict[str, float]:
    rng = np.random.default_rng(777001)
    theta_ref = np.array([0.52, 0.22, -0.18, 0.14, 0.10, -0.12])
    theta_drift = theta_ref + np.array([0.01, -0.01, 0.00, 0.01, 0.00, -0.01])
    theta_swap = np.array([-0.30, 0.40, 0.35, -0.22, 0.28, 0.25])

    initials = rng.uniform(-0.7, 0.7, size=cfg.df_probe_n)
    exo = rng.normal(0, 0.6, size=(cfg.df_probe_n, cfg.df_horizon, 5))

    short_ref, short_drift, short_swap = [], [], []
    long_ref, long_drift, long_swap = [], [], []
    for i in range(cfg.df_probe_n):
        rr = rollout(initials[i], exo[i], theta_ref)
        rd = rollout(initials[i], exo[i], theta_drift)
        rs = rollout(initials[i], exo[i], theta_swap)
        short_ref.append(rr[0]); short_drift.append(rd[0]); short_swap.append(rs[0])
        long_ref.append(rr); long_drift.append(rd); long_swap.append(rs)

    short_ref = np.asarray(short_ref)
    short_drift = np.asarray(short_drift)
    short_swap = np.asarray(short_swap)
    long_ref = np.asarray(long_ref)
    long_drift = np.asarray(long_drift)
    long_swap = np.asarray(long_swap)

    d_short_drift = float(np.sqrt(np.mean((short_ref-short_drift)**2)))
    d_short_swap = float(np.sqrt(np.mean((short_ref-short_swap)**2)))
    d_long_drift = float(np.sqrt(np.mean((long_ref-long_drift)**2)))
    d_long_swap = float(np.sqrt(np.mean((long_ref-long_swap)**2)))

    # Known-lineage handoff vs independent same-rule clone.
    exo_line = rng.normal(0, 0.5, size=(64, 5))
    seg1 = rollout(0.15, exo_line[:32], theta_ref)
    end_state = float(seg1[-1])
    h_end = np.array([np.mean(exo_line[:32, 0]), np.mean(exo_line[:32, 1])])
    b_end = float(np.tanh(0.7*end_state + 0.2*h_end[0] - 0.1*h_end[1]))

    # Positive: same causal lineage continues exactly from handoff.
    c_lineage = continuity_score(True, end_state, end_state, h_end, h_end, b_end, b_end)
    # Negative: independent clone with same rule and even matching handoff values.
    c_clone = continuity_score(False, end_state, end_state, h_end, h_end, b_end, b_end)

    passed = (
        d_short_drift < cfg.epsilon_F_short
        and d_long_drift < cfg.epsilon_F_long
        and d_short_swap > cfg.epsilon_F_short
        and d_long_swap > cfg.epsilon_F_long
        and c_lineage > cfg.tau_C
        and c_clone < cfg.tau_C
    )
    return {
        "output_scale": "[-1,1] via tanh",
        "dF_short_ref_drift": d_short_drift,
        "dF_short_ref_swap": d_short_swap,
        "epsilon_F_short": cfg.epsilon_F_short,
        "dF_long_ref_drift": d_long_drift,
        "dF_long_ref_swap": d_long_swap,
        "epsilon_F_long": cfg.epsilon_F_long,
        "C_known_lineage": c_lineage,
        "C_independent_same_rule_clone": c_clone,
        "tau_C": cfg.tau_C,
        "pass": bool(passed),
        "interpretation": "Synthetic discrimination of update-law continuity + known causal lineage only; not a validation of personal identity.",
    }


def plot_component_status(component_summary: Dict[str, Dict], out: Path) -> None:
    names = list(component_summary)
    vals = [component_summary[n]["relative_degradation"][0] for n in names]
    plt.figure(figsize=(7.2, 4.6))
    plt.axhline(0.0, linewidth=1)
    plt.bar(names, vals)
    plt.ylabel("Relative degradation vs retrained FULL")
    plt.title("Matched-information component audit")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(out / "component_retrained_audit.png", dpi=220)
    plt.close()


def plot_null(null_ci: Tuple[float,float,float], cfg: FrozenConfig, out: Path) -> None:
    point, lo, hi = null_ci
    plt.figure(figsize=(5.8, 4.4))
    plt.errorbar([0], [point], yerr=[[point-lo],[hi-point]], fmt="o", capsize=5)
    plt.axhline(0.0, linewidth=1)
    plt.axhline(cfg.null_equiv_margin, linewidth=1, linestyle="--")
    plt.axhline(-cfg.null_equiv_margin, linewidth=1, linestyle="--")
    plt.xlim(-1,1); plt.xticks([0],["STATE_SUFFICIENT"])
    plt.ylabel("Relative MSE difference: FULL_EXTRA vs BASE_S")
    plt.title("Practical-equivalence negative control")
    plt.tight_layout()
    plt.savefig(out / "state_sufficient_equivalence.png", dpi=220)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results/coreno_self_phase0a_v1_1")
    parser.add_argument("--quick", action="store_true", help="Smoke test only; not a frozen QUAL run")
    args = parser.parse_args()

    cfg = FrozenConfig()
    if args.quick:
        cfg = FrozenConfig(n_seeds=6, n_trajectories=18, steps_per_trajectory=36,
                           bootstrap_reps=2000, df_probe_n=512, df_horizon=16)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "config_frozen.json").write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2), encoding="utf-8")

    full_rows, null_rows, hist_rows = [], [], []
    for i in range(cfg.n_seeds):
        full_rows.append(evaluate_seed(cfg.full_seed_start+i, cfg, "FULL"))
        null_rows.append(evaluate_seed(cfg.null_seed_start+i, cfg, "STATE_SUFFICIENT"))
        hist_rows.append(history_order_audit(cfg.history_seed_start+i, cfg))

    full_df = pd.DataFrame(full_rows)
    null_df = pd.DataFrame(null_rows)
    hist_df = pd.DataFrame(hist_rows)
    full_df.to_csv(out / "seed_results_full.csv", index=False)
    null_df.to_csv(out / "seed_results_state_sufficient.csv", index=False)
    hist_df.to_csv(out / "history_order_causal_audit.csv", index=False)

    rng = np.random.default_rng(cfg.bootstrap_seed)

    # Original M0-M3 information ladder: diagnostic only.
    q_num = full_df["info_mse_M3"].to_numpy()
    best_baseline = np.minimum.reduce([
        full_df["info_mse_M0"].to_numpy(),
        full_df["info_mse_M1"].to_numpy(),
        full_df["info_mse_M2"].to_numpy(),
    ])
    q_info = seed_boot_ratio(q_num, best_baseline, cfg.bootstrap_reps, rng)

    # Retrained component audits with matched oracle-U availability.
    component_summary = {}
    for comp, reduced in [("boundary","NO_B"),("history_predictor","NO_H"),("access","NO_A")]:
        full = full_df["struct_mse_FULL"].to_numpy()
        red = full_df[f"struct_mse_{reduced}"].to_numpy()
        rel = (red-full)/full
        ci = seed_boot_ci(rel, cfg.bootstrap_reps, rng)
        component_summary[comp] = {
            "relative_degradation": list(ci),
            "status": classify_component(ci, cfg),
            "comparison": f"retrained FULL vs retrained {reduced}",
        }

    # U removal is diagnostic only because U is oracle in this phase.
    full = full_df["struct_mse_FULL"].to_numpy()
    nou = full_df["struct_mse_NO_U"].to_numpy()
    u_rel = seed_boot_ci((nou-full)/full, cfg.bootstrap_reps, rng)

    # STATE_SUFFICIENT practical equivalence: relative difference must fit entirely inside +/-2%.
    base_s = null_df["null_mse_BASE_S"].to_numpy()
    full_extra = null_df["null_mse_FULL_EXTRA"].to_numpy()
    null_rel = seed_boot_ci((full_extra-base_s)/base_s, cfg.bootstrap_reps, rng)
    null_equiv = bool(null_rel[1] >= -cfg.null_equiv_margin and null_rel[2] <= cfg.null_equiv_margin)

    # History order causal audit + carrier erasure control.
    hist_ci = seed_boot_ci(hist_df["history_order_abs_effect"].to_numpy(), cfg.bootstrap_reps, rng)
    erased_ci = seed_boot_ci(hist_df["history_erased_abs_effect"].to_numpy(), cfg.bootstrap_reps, rng)
    hist_causal_pass = bool(hist_ci[1] > cfg.history_causal_min_effect)
    erased_pass = bool(erased_ci[2] < cfg.history_erased_max_effect)

    identity = identity_audit(cfg)

    # Conservative localization; equivalence and inconclusive are distinct.
    failures = []
    reductions = []
    inconclusive = []
    for comp, s in component_summary.items():
        status = s["status"]
        if status == "PRACTICALLY_EQUIVALENT":
            reductions.append(comp)
        elif status == "INCONCLUSIVE":
            inconclusive.append(comp)

    if not null_equiv:
        failures.append("STATE_SUFFICIENT_EQUIVALENCE_FAIL")
    if not hist_causal_pass:
        failures.append("HISTORY_ORDER_CAUSAL_SUPPORT_FAIL")
    if not erased_pass:
        failures.append("HISTORY_CARRIER_ERASURE_CONTROL_FAIL")
    if not identity["pass"]:
        failures.append("IDENTITY_OPERATIONALIZATION_FAIL")

    # Overall PASS requires supported B/H/A components, valid negative control, history causal audit, identity audit.
    all_components_supported = all(v["status"] == "SUPPORTED_COMPONENT" for v in component_summary.values())
    qual_pass = bool(all_components_supported and null_equiv and hist_causal_pass and erased_pass and identity["pass"])

    if qual_pass:
        final_decision = "SYNTHETIC_QUAL_PASS"
    elif reductions:
        final_decision = "COMPONENT_EQUIVALENCE_REDUCE_THEORY"
    elif inconclusive:
        final_decision = "INCONCLUSIVE_COMPONENT_NECESSITY"
    else:
        final_decision = "QUAL_FAIL"

    summary = {
        "phase": "CORENO Self Phase 0A v1.1 — Minimal Synthetic Qualification",
        "synthetic_only": True,
        "oracle_U_warning": "U_t is oracle latent. Q_info and U-removal are information-set diagnostics, not architecture evidence.",
        "information_ladder_Q_M3_vs_best_M0_M2": {"point": q_info[0], "ci95": [q_info[1], q_info[2]], "gate": False},
        "matched_retrained_components": component_summary,
        "oracle_U_removal_diagnostic": {"relative_degradation": list(u_rel), "gate": False},
        "state_sufficient_equivalence": {
            "relative_difference": list(null_rel),
            "frozen_margin": [-cfg.null_equiv_margin, cfg.null_equiv_margin],
            "pass": null_equiv,
        },
        "history_order_causal_audit": {
            "order_effect": list(hist_ci),
            "minimum_effect": cfg.history_causal_min_effect,
            "order_effect_pass": hist_causal_pass,
            "carrier_erased_effect": list(erased_ci),
            "maximum_erased_effect": cfg.history_erased_max_effect,
            "carrier_erasure_pass": erased_pass,
        },
        "identity_audit": identity,
        "reductions": reductions,
        "inconclusive_components": inconclusive,
        "failures": failures,
        "final_decision": final_decision,
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    decision = {
        "CURRENT_GATE": "PHASE_0A_V1_1_SYNTHETIC_QUAL",
        "FINAL_DECISION": final_decision,
        "AUTHORIZED_IF_PASS": [
            "The frozen synthetic decomposition is numerically distinguishable under matched retraining and frozen margins.",
            "History-order intervention changes the regenerated carrier and downstream response in this synthetic generator.",
            "The frozen d_F + known-lineage C audit distinguishes small drift, rule swap, and an independent same-rule clone in this synthetic setup."
        ],
        "NOT_AUTHORIZED": [
            "human selfhood validated", "consciousness or qualia explained", "soul or afterlife supported",
            "fixed core disproved", "real latent states measured", "personal identity proven by d_F alone"
        ],
        "REDUCE_ONLY_IF_EQUIVALENT": reductions,
        "DO_NOT_REDUCE_IF_INCONCLUSIVE": inconclusive,
        "NEXT_AUTHORIZED_STEP": (
            "If SYNTHETIC_QUAL_PASS: Phase 0B non-oracle U_hat estimation with all Phase 0A gates frozen. "
            "If component equivalence: instantiate the corresponding reduced model. "
            "If inconclusive: increase precision without changing effect thresholds or generator parameters."
        )
    }
    (out / "decision.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")

    plot_component_status(component_summary, out)
    plot_null(null_rel, cfg, out)

    # Manifest after all outputs except manifest itself.
    manifest = {}
    for p in sorted(out.iterdir()):
        if p.is_file():
            manifest[p.name] = sha256_file(p)
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    audit = [
        "# CORENO Self Phase 0A v1.1 Audit Log", "",
        f"- quick_mode: {args.quick}",
        f"- final_decision: {final_decision}",
        f"- oracle_U: true (synthetic only)",
        f"- seed_level_bootstrap: true",
        f"- coherent_access_twins: true",
        f"- history_order_before_carrier_regeneration: true",
        f"- reduced_models_retrained: true",
        f"- null_equivalence_margin: +/-{cfg.null_equiv_margin:.3f}",
        f"- boundary_status: {component_summary['boundary']['status']}",
        f"- history_predictor_status: {component_summary['history_predictor']['status']}",
        f"- access_status: {component_summary['access']['status']}",
        "", "Claim firewall: synthetic qualification only."
    ]
    (out / "audit_log.md").write_text("\n".join(audit), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
