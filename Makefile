.PHONY: install smoke qual

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

smoke:
	python phase0a/src/coreno_self_phase0a_v1_1.py --out results/smoke_v1_1 --quick

qual:
	python phase0a/src/coreno_self_phase0a_v1_1.py --out results/coreno_self_phase0a_v1_1
