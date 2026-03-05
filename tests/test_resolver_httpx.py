import asyncio
from srpt.resolver import resolve


async def test_resolve_httpx():
    print("Resolving httpx...")
    candidates = await resolve(["httpx"])
    for c in candidates:
        print(f"  {c.name}=={c.version}")


if __name__ == "__main__":
    asyncio.run(test_resolve_httpx())
