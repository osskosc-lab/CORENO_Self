# CORENO Self Phase 0A v1.1

監査指摘を反映した修正版です。

## 主な修正
- M3のoracle U優位を構造的証拠から分離
- STATE_SUFFICIENTを±2%の事前固定同等幅で監査
- 境界・履歴・アクセスは縮小モデルを再学習
- 履歴順序介入後に履歴担体Hを再生成
- アクセスは観測作用素・境界・targetを一貫して再生成
- bootstrapはseed単位で対応保持
- identity auditはd_F(short/long)+C(Gamma1,Gamma2)>tau_C
- 境界FAILをEQUIVALENTとINCONCLUSIVEに分離

## Smoke test
```bash
python phase0a/src/coreno_self_phase0a_v1_1.py --out results/smoke_v1_1 --quick
```
これは技術確認のみで、QUAL判定には使いません。

## Frozen run
```bash
python phase0a/src/coreno_self_phase0a_v1_1.py --out results/coreno_self_phase0a_v1_1
```

## Claim Firewall
このPhase 0Aは合成系の操作化適格性のみを監査します。人間の自己、意識、クオリア、魂、死後継続、固定核不存在を実証しません。U_tはoracle latentです。

## Decision discipline
- `SUPPORTED_COMPONENT`: 事前固定support marginを95%CI下限が超える
- `PRACTICALLY_EQUIVALENT`: 95%CI全体が事前固定equivalence幅に入る
- `INCONCLUSIVE`: 上記どちらにも該当しない。理論を縮小しない
- `SYNTHETIC_QUAL_PASS`: 凍結仕様の全必須ゲートを通過した合成系QUALのみ
