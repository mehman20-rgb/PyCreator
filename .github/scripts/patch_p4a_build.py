#!/usr/bin/env python3
"""Apply a safe multi-architecture virtualenv fix to python-for-android."""

from pathlib import Path
import sys


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(
            f"{label}: expected exactly one upstream block, found {count}. "
            "The python-for-android source has changed; refusing an unsafe patch."
        )
    return source.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch_p4a_build.py PATH_TO_build.py")

    build_file = Path(sys.argv[1])
    if not build_file.is_file():
        raise SystemExit(f"python-for-android build.py not found: {build_file}")

    source = build_file.read_text(encoding="utf-8")

    old_venv = """    # Use our hostpython to create the virtualenv
    host_python = sh.Command(ctx.hostpython)
    with current_directory(join(ctx.build_dir)):
        shprint(host_python, '-m', 'venv', 'venv')
"""
    new_venv = """    # p4a calls this function once per architecture, but both
    # architectures share ctx.build_dir and therefore share one venv.
    # Initialize it only once instead of rerunning venv over an active env.
    host_python = sh.Command(ctx.hostpython)
    with current_directory(join(ctx.build_dir)):
        venv_python = join(ctx.build_dir, "venv", "bin", "python")
        if not exists(venv_python):
            shprint(host_python, '-m', 'venv', 'venv')
        else:
            info('Reusing shared hostpython virtualenv for {}'.format(arch.arch))
"""

    old_pip = """        # Prepare base environment and upgrade pip:
        base_env = dict(copy.copy(os.environ))
        base_env["PYTHONPATH"] = ctx.get_site_packages_dir(arch)
        info('Upgrade pip to latest version')
        shprint(sh.bash, '-c', (
            "source venv/bin/activate && pip install -U pip"
        ), _env=copy.copy(base_env))
"""
    new_pip = """        # Prepare base environment and upgrade pip once for the shared venv.
        base_env = dict(copy.copy(os.environ))
        base_env["PYTHONPATH"] = ctx.get_site_packages_dir(arch)
        pip_ready_marker = join(ctx.build_dir, "venv", ".p4a-pip-ready")
        if not exists(pip_ready_marker):
            info('Upgrade pip once for the shared multi-architecture virtualenv')
            shprint(sh.bash, '-c', (
                "source venv/bin/activate && python -m pip install -U pip && touch venv/.p4a-pip-ready"
            ), _env=copy.copy(base_env))
        else:
            info('Reuse pip initialized for the first target architecture')
"""

    if new_venv in source and new_pip in source:
        print("python-for-android multi-architecture virtualenv patch already applied.")
        return

    source = replace_once(source, old_venv, new_venv, "virtualenv initialization")
    source = replace_once(source, old_pip, new_pip, "pip upgrade")

    build_file.write_text(source, encoding="utf-8")
    print(f"Patched {build_file}: shared venv and pip are initialized only once.")


if __name__ == "__main__":
    main()
