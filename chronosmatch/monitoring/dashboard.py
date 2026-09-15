def print_snapshot(stats):
    print("\033[2J\033[H", end="")
    print("CHRONOSMATCH")
    print("=" * 50)
    for key, value in stats.items():
        print(f"{key:<25} {value}")
