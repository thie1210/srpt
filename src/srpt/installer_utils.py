import asyncio
from pathlib import Path
from typing import Dict, Optional, Tuple


def install_single_wheel(
    wheel_path: Path,
    schemes: Dict[str, str],
    venv_python: Path,
    script_kind: str,
) -> Tuple[bool, Optional[str]]:
    """
    Install a single wheel file synchronously.

    This function is designed to run in a thread pool via asyncio.to_thread().

    Args:
        wheel_path: Path to the wheel file
        schemes: Dictionary mapping scheme names to target directories
        venv_python: Path to the Python interpreter in the venv
        script_kind: Script kind for the installer (e.g., "posix" or "win-amp")

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    from installer import install
    from installer.destinations import SchemeDictionaryDestination
    from installer.sources import WheelFile

    try:
        with WheelFile.open(wheel_path) as source:
            destination = SchemeDictionaryDestination(
                schemes, interpreter=str(venv_python), script_kind=script_kind
            )
            install(source, destination, additional_metadata={})
        return (True, None)
    except Exception as e:
        return (False, str(e))


async def install_wheels_parallel(
    wheel_paths: list[Path],
    target_dir: Path,
    venv_python: Path,
) -> list[Tuple[str, bool, Optional[str]]]:
    """
    Install multiple wheels in parallel with a progress bar.

    Args:
        wheel_paths: List of paths to wheel files
        target_dir: Target directory for installation (site-packages)
        venv_python: Path to the Python interpreter in the venv

    Returns:
        List of tuples (package_name, success, error_message)
    """
    from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn, TimeElapsedColumn

    if not wheel_paths:
        return []

    schemes = {
        "purelib": str(target_dir),
        "platlib": str(target_dir),
        "headers": str(target_dir / "include"),
        "scripts": str(target_dir / "bin"),
        "data": str(target_dir / "data"),
    }

    import os

    for scheme_path in schemes.values():
        Path(scheme_path).mkdir(parents=True, exist_ok=True)

    script_kind = "posix" if os.name == "posix" else "win-amp"

    results: list[Tuple[str, bool, Optional[str]]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        task_id = progress.add_task("Installing wheels", total=len(wheel_paths))

        async def install_one(wheel_path: Path) -> Tuple[str, bool, Optional[str]]:
            """Install a single wheel and update progress."""
            success, error = await asyncio.to_thread(
                install_single_wheel,
                wheel_path,
                schemes,
                venv_python,
                script_kind,
            )
            progress.update(task_id, advance=1)
            package_name = wheel_path.stem.split("-")[0] if wheel_path.stem else str(wheel_path)
            return (package_name, success, error)

        results = await asyncio.gather(*[install_one(wp) for wp in wheel_paths])

    return results
