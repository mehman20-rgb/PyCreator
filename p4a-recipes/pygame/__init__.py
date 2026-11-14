"""Android-compatible Pygame recipe for CPython 3.14.

The upstream p4a recipe pins Pygame 2.1.0, whose generated C sources
include the removed CPython header longintrepr.h. Build from the 2.6.1
GitHub source archive so Cython regenerates the extension against the
active Python headers.
"""
from pathlib import Path

from pythonforandroid.recipes.pygame import Pygame2Recipe
from pythonforandroid.toolchain import current_directory


class Pygame261Recipe(Pygame2Recipe):
    version = "2.6.1"
    url = "https://github.com/pygame/pygame/archive/{version}.tar.gz"
    hostpython_prerequisites = ["setuptools", "cython>=3.1"]

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            # _sprite is an optional Cython accelerator. pygame.sprite itself
            # remains available in Python; omitting this accelerator avoids
            # a separate Cython 3.1 incompatibility.
            setup_path = Path("Setup")
            if setup_path.exists():
                lines = setup_path.read_text().splitlines()
                lines = [
                    line for line in lines
                    if not line.lstrip().startswith("_sprite ")
                ]
                setup_path.write_text("\n".join(lines) + "\n")

            optional_pyx = Path("src_c/_sprite.pyx")
            if optional_pyx.exists():
                optional_pyx.unlink()


recipe = Pygame261Recipe()
