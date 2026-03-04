import asyncio
from py.pypi import PyPIClient


async def test_pypi():
    client = PyPIClient()
    try:
        metadata = await client.get_project_metadata("requests")
        print(f"Project: {metadata.get('name')}")
        files = metadata.get("files", [])
        print(f"Found {len(files)} files for requests")
        if files:
            print(f"Example file: {files[0].get('filename')}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_pypi())
