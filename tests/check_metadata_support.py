import asyncio
from py.pypi import PyPIClient


async def check_metadata():
    client = PyPIClient()
    metadata = await client.get_project_metadata("requests")
    for file in metadata.get("files", []):
        if file.get("metadata"):
            print(f"File {file['filename']} HAS separate metadata!")
            return
    print("No files found with separate metadata.")


if __name__ == "__main__":
    asyncio.run(check_metadata())
