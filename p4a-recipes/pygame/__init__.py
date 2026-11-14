"""Android-compatible Pygame recipe for CPython 3.14.

Pygame 2.6.1 contains a Cython extension declaration for Sprite.__dict__.
With current Cython 3.1, assigning to that special attribute in __cinit__
is rejected: the extension type's dictionary is allocated automatically.
Patch only that obsolete assignment while keeping the full pygame.sprite
extension and every other Pygame component in the build.
"""
from pathlib import Path

from pythonforandroid.recipes.pygame import Pygame2Recipe


class Pygame261Recipe(Pygame2Recipe):
    version = "2.6.1"
    url = "https://github.com/pygame/pygame/archive/{version}.tar.gz"
    hostpython_prerequisites = ["setuptools", "cython>=3.1"]

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)

        sprite_source = (
            Path(self.get_build_dir(arch.arch))
            / "src_c"
            / "cython"
            / "pygame"
            / "_sprite.pyx"
        )
        if sprite_source.exists():
            source = sprite_source.read_text(encoding="utf-8")
            obsolete_init = "        self.__dict__ = {}\n"
            if obsolete_init in source:
                source = source.replace(obsolete_init, "", 1)
                sprite_source.write_text(source, encoding="utf-8")


recipe = Pygame261Recipe()
