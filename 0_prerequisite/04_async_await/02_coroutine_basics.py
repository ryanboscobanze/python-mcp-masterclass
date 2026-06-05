import asyncio


# ─── REGULAR FUNCTION ───────────────────────────────────────────────────────
# Calling it runs it immediately and returns the value.

def greet():
    return "Hello"


# ─── COROUTINE FUNCTION ─────────────────────────────────────────────────────
# Adding `async` makes it a coroutine function.
# Calling it does NOT run it — it returns a coroutine object (a paused task).
# You need to await it to actually execute it.

async def greet_async():
    return "Hello from async"


async def main():
    # Regular function — runs immediately
    result = greet()
    print(result)                   # Hello

    # Coroutine function — calling without await gives you the object, not the value
    coro = greet_async()
    print(type(coro))               # <class 'coroutine'>
    coro.close()                    # discard it cleanly

    # await actually runs it and gives you the return value
    result = await greet_async()
    print(result)                   # Hello from async


if __name__ == "__main__":
    asyncio.run(main())
