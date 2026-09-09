import unittest
import numpy as np

from phase0a.src.coreno_self_phase0a_v1_1 import (
    FrozenConfig,
    INFO_FEATURES,
    STRUCT_FEATURES,
    NULL_FEATURES,
    classify_component,
    history_carrier_from_events,
    identity_audit,
)


class FrozenContractTests(unittest.TestCase):
    def test_frozen_scale(self):
        cfg = FrozenConfig()
        self.assertEqual(cfg.n_seeds, 64)
        self.assertEqual(cfg.n_trajectories, 48)
        self.assertEqual(cfg.steps_per_trajectory, 64)
        self.assertEqual(cfg.bootstrap_reps, 20000)
        self.assertEqual(cfg.bootstrap_seed, 90210)

    def test_frozen_margins(self):
        cfg = FrozenConfig()
        self.assertEqual(cfg.component_support_margin, 0.05)
        self.assertEqual(cfg.component_equiv_margin, 0.02)
        self.assertEqual(cfg.null_equiv_margin, 0.02)
        self.assertEqual(cfg.history_causal_min_effect, 0.05)
        self.assertEqual(cfg.history_erased_max_effect, 0.01)
        self.assertEqual(cfg.epsilon_F_short, 0.10)
        self.assertEqual(cfg.epsilon_F_long, 0.15)
        self.assertEqual(cfg.tau_C, 0.80)

    def test_oracle_u_is_nonexclusive_in_structural_component_family(self):
        # B/H/A component necessity must be tested with matched oracle-U availability.
        for name in ["FULL", "NO_B", "NO_H", "NO_A"]:
            self.assertIn("U0", STRUCT_FEATURES[name])
            self.assertIn("U1", STRUCT_FEATURES[name])

    def test_information_ladder_keeps_oracle_u_only_in_m3(self):
        self.assertNotIn("U0", INFO_FEATURES["M0"])
        self.assertNotIn("U0", INFO_FEATURES["M1"])
        self.assertNotIn("U0", INFO_FEATURES["M2"])
        self.assertIn("U0", INFO_FEATURES["M3"])

    def test_state_sufficient_control_has_s_only_baseline(self):
        self.assertEqual(NULL_FEATURES["BASE_S"], ["S0", "S1", "S2"])
        self.assertTrue(set(NULL_FEATURES["BASE_S"]).issubset(NULL_FEATURES["FULL_EXTRA"]))

    def test_component_classification_three_way(self):
        cfg = FrozenConfig()
        self.assertEqual(
            classify_component((0.08, 0.06, 0.10), cfg),
            "SUPPORTED_COMPONENT",
        )
        self.assertEqual(
            classify_component((0.00, -0.01, 0.01), cfg),
            "PRACTICALLY_EQUIVALENT",
        )
        self.assertEqual(
            classify_component((0.03, 0.00, 0.06), cfg),
            "INCONCLUSIVE",
        )

    def test_history_carrier_is_order_sensitive(self):
        events = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [-1.0, 0.5],
            [0.2, -0.3],
        ])
        a = history_carrier_from_events(events, np.array([0, 1, 2, 3]), 0.78)
        b = history_carrier_from_events(events, np.array([3, 1, 0, 2]), 0.78)
        self.assertGreater(np.linalg.norm(a - b), 0.0)

    def test_identity_audit_requires_rule_distance_and_lineage(self):
        result = identity_audit(FrozenConfig(df_probe_n=256, df_horizon=8))
        self.assertLess(result["dF_short_ref_drift"], result["epsilon_F_short"])
        self.assertGreater(result["dF_short_ref_swap"], result["epsilon_F_short"])
        self.assertLess(result["dF_long_ref_drift"], result["epsilon_F_long"])
        self.assertGreater(result["dF_long_ref_swap"], result["epsilon_F_long"])
        self.assertGreater(result["C_known_lineage"], result["tau_C"])
        self.assertLess(result["C_independent_same_rule_clone"], result["tau_C"])
        self.assertTrue(result["pass"])


if __name__ == "__main__":
    unittest.main()
