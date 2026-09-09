# CORENO Self Phase 0A v1.1 — Spec Amendment

一次監査で指摘された6点を凍結仕様へ反映した。

1. **Oracle U confound** — M0-M3は情報集合ラダーとしてのみ報告。構造成分判定はoracle Uを共有した再学習縮小モデルで行う。
2. **Negative control** — STATE_SUFFICIENTは「有意差なし」ではなく、relative MSE差の95%CIが事前固定±2%内に入る実用同等性を要求。
3. **Boundary necessity** — Bを定数化した入力破壊ではなく、NO_Bをゼロから再学習。SUPPORTED / PRACTICALLY_EQUIVALENT / INCONCLUSIVEの3値判定。
4. **History causality** — 入力shuffleは因果証拠から除外。同じevent multisetの順序を変えた後にHを再生成し、下流応答をpaired監査。H=0のerasure controlも要求。
5. **Access relativity** — label-only swapを禁止。同一潜在状態からaccess-specific observation/B/Yを一貫して生成するcoherent twinsを使用。
6. **Identity criterion** — d_Fをone-stepとlong-horizonに分け、tanhで出力尺度[-1,1]を固定。さらにC(Gamma1,Gamma2)>tau_Cを実装し、独立same-rule cloneを負対照にする。

元論文の「No Fixed Core」は存在論的断定ではなく、今後は **The model does not assume an invariant core / 本モデルは不変核を仮定しない** と表現する。
