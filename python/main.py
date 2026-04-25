import os
from scheduler import Scheduler

BUILD_DIR = os.path.join(os.path.dirname(__file__), "..", "build", "models")

if __name__ == "__main__":
    sched = Scheduler()
    sched.load_models_from_dir(BUILD_DIR)

    print(f"Loaded {len(sched.models)} model(s):")
    for m in sorted(sched.models, key=lambda m: m.order):
        stop = f"{m.stop_time:.3f} s" if m.stop_time >= 0 else "sim end"
        print(f"  [{m.order:3d}] {m.name:30s}  {m.update_rate} Hz  stop={stop}")
    print()

    sched.run(duration=0.05)  # 50 ms of simulation time
