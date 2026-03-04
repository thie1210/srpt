import asyncio
from py.pypi import PyPIClient


async def get_wheel_url():
    client = PyPIClient()
    metadata = await client.get_project_metadata("requests")
    # Find latest version files
    for file in metadata.get("files", []):
        if file.get("filename", "").endswith("-py3-none-any.whl"):
            print(f"requests: {file.get('url')}")
            break

    metadata = await client.get_project_metadata("idna")
    for file in metadata.get("files", []):
        if file.get("filename", "").endswith("-py3-none-any.whl"):
            print(f"idna: {file.get('url')}")
            break


if __name__ == "__main__":
    asyncio.run(get_wheel_url())
