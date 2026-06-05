import asyncio
import time


# ─── SYNCHRONOUS ────────────────────────────────────────────────────────────
# Each call blocks until it finishes — nothing else can run while it waits.

def fetch_sync(name):
    print(f"  [{name}] fetching...")
    time.sleep(2)
    print(f"  [{name}] done")
    return {"result": name}


def run_sync():
    start = time.time()
    fetch_sync("request-1")
    fetch_sync("request-2")
    fetch_sync("request-3")
    print(f"\nSync total: {time.time() - start:.1f}s\n")


# ─── ASYNCHRONOUS ───────────────────────────────────────────────────────────
# All three start immediately. While one is waiting, the others keep going.

async def fetch_async(name):
    print(f"  [{name}] fetching...")
    await asyncio.sleep(2)
    print(f"  [{name}] done")
    return {"result": name}


async def run_async():
    start = time.time()
    await asyncio.gather(
        fetch_async("request-1"),
        fetch_async("request-2"),
        fetch_async("request-3"),
    )
    print(f"\nAsync total: {time.time() - start:.1f}s\n")


# ─── ENTRY POINT ────────────────────────────────────────────────────────────

async def main():
    print("=== SYNC (blocks on each call) ===")
    run_sync()

    print("=== ASYNC (all run concurrently) ===")
    await run_async()


if __name__ == "__main__":
    asyncio.run(main())


# The key mental model: await means "I'm waiting, go do something
# else" — gather means "schedule all of these concurrently so they
# interleave at their await points instead of running one after another"

# async def — marks a function as one that can pause. That's it.

# await — the pause point. When Python hits await asyncio.sleep(2), 
# it pauses that function and goes to do other work. 

# asyncio — the Python library that manages all of this. 
# It runs an event loop — a scheduler that watches all paused functions 
# and wakes them up when they're ready.

# asyncio.gather() — hands multiple coroutines to the event loop at the 
# same time. Instead of starting one, waiting, then starting the next — 
# all three start immediately and the event loop juggles them while they wait.