import asyncio
import time


# ─── SEQUENTIAL AWAIT ───────────────────────────────────────────────────────
# Each step waits for the previous one to finish before starting.
# Use this when step two depends on step one's result.

async def step_one():
    await asyncio.sleep(1)
    return "step one result"


async def step_two(input_data: str):
    await asyncio.sleep(0.5)
    return f"processed: {input_data}"


async def run_sequential():
    start = time.time()
    data = await step_one()         # wait for step one
    output = await step_two(data)   # then run step two with its result
    print(f"Sequential: {output!r} — took {time.time() - start:.1f}s")


# ─── CONCURRENT AWAIT ───────────────────────────────────────────────────────
# asyncio.gather() runs all coroutines at the same time.
# Total time = slowest task, not sum of all tasks.

async def fetch_tool(name: str, delay: float):
    await asyncio.sleep(delay)
    return f"{name} result"


async def run_concurrent():
    start = time.time()

    # These three run simultaneously — total ~1s, not 1+0.5+0.8=2.3s
    results = await asyncio.gather(
        fetch_tool("tool_call",    1.0),
        fetch_tool("resource_read", 0.5),
        fetch_tool("prompt_fetch",  0.8),
    )

    for r in results:
        print(f"  {r}")
    print(f"Concurrent: took {time.time() - start:.1f}s")


# ─── ENTRY POINT ────────────────────────────────────────────────────────────

async def main():
    print("=== Sequential (step two needs step one's output) ===")
    await run_sequential()

    print("\n=== Concurrent (independent tasks, run together) ===")
    await run_concurrent()


if __name__ == "__main__":
    asyncio.run(main())
