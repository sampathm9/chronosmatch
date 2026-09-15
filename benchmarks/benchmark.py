import subprocess
import sys
import time

N = 100_000
start = time.perf_counter()
result = subprocess.run(
    [sys.executable, "app.py", "--orders", str(N)],
    text=True,
)
elapsed = time.perf_counter() - start
print(f"Total process wall time: {elapsed:.6f}s")
print(f"End-to-end process rate: {N / elapsed:,.0f} orders/sec")
raise SystemExit(result.returncode)
