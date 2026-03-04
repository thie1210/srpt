import asyncio
from py.resolver import resolve


async def test_resolve():
    print("Py: Resolving 'requests' (with transitive deps)...")
    try:
        candidates = await resolve(["requests"])
        for candidate in candidates:
            print(f"Resolved: {candidate.name}=={candidate.version}")
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_resolve())
