# ChronosMatch

End-to-end zero-copy trading-engine prototype:
asyncio market firehose -> mmap ring buffer -> Cython matching engine -> SQLite ledger.

## Setup

Windows PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
python setup.py build_ext --inplace
python app.py
```

Linux/macOS:
```bash
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python setup.py build_ext --inplace
python app.py
```

Benchmark:
```bash
python benchmarks/benchmark.py
```

This is a learning/portfolio prototype. Latency is host-dependent and is not a claim of exchange-grade HFT performance.
