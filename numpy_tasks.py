import sys, time, json, numpy as np


def matmul(n=2000):
    a = np.random.rand(n, n).astype(np.float64)
    b = np.random.rand(n, n).astype(np.float64)
    t0 = time.perf_counter()
    c = a @ b
    dt = time.perf_counter() - t0
    print(json.dumps({"task": "numpy.matmul", "n": n, "seconds": dt}))


def elem(n=1_000_000, it=50):
    a = np.random.rand(n).astype(np.float64)
    t0 = time.perf_counter()
    for _ in range(it):
        a = np.sin(a) + np.cos(a) * np.tan(a)
    dt = time.perf_counter() - t0
    print(json.dumps({"task": "numpy.elemwise", "n": n, "iter": it, "seconds": dt}))


if __name__ == "__main__":
    sub = sys.argv[1] if len(sys.argv) > 1 else "matmul"
    if sub == "matmul":
        matmul(int(sys.argv[2]) if len(sys.argv) > 2 else 2000)
    elif sub == "elem":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000
        it = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        elem(n, it)
    else:
        print(json.dumps({"error": "unknown subcommand", "sub": sub}))
        sys.exit(2)
