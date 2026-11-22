### Autonomous run

**You own the exit condition. Define done, then drive to it without stopping.**

1. State the exit condition as a checkable predicate before the first iteration (tests green, repro fixed, all N PRs merged, pixel-diff zero).
2. Use an authorized native watcher or scheduled heartbeat when the host supports it. Choose an interval that makes sense for the event. Record its actual handle and how to cancel it. If no wake mechanism is available, work within the current run and checkpoint the remaining work. A checkpoint alone cannot wake the host.

**Reply:** the exit condition, iterations run, what landed, what was discarded, final predicate state.
