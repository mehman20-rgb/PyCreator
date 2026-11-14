"""Android-compatible Pygame recipe for CPython 3.14.

Pygame's optional Cython sprite accelerator uses an obsolete explicit
assignment to the extension type's __dict__. Cython 3 rejects that assignment.
The extension and pygame.sprite API are retained; only the redundant
initialization statement is patched before compilation.
"""
from pathlib import Path

from pythonforandroid.recipes.pygame import Pygame2Recipe


class Pygame261Recipe(Pygame2Recipe):
    version = "2.6.1"
    url = "https://github.com/pygame/pygame/archive/{version}.tar.gz"
    hostpython_prerequisites = ["setuptools", "cython>=3.1"]

    def _patch_cython_sprite_source(self, arch):
        build_dir = Path(self.get_build_dir(arch.arch))
        sprite_source = (
            build_dir / "src_c" / "cython" / "pygame" / "_sprite.pyx"
        )

        if not sprite_source.is_file():
            raise RuntimeError(
                "Pygame source is missing _sprite.pyx; cannot apply "
                "the Python 3.14/Cython compatibility patch."
            )

        source = sprite_source.read_text(encoding="utf-8")
        obsolete = "        self.__dict__ = {}"
        if obsolete in source:
            source = source.replace(
                obsolete,
                "        # __dict__ is initialized by Cython for this extension type.",
                1,
            )
            sprite_source.write_text(source, encoding="utf-8")

    def build_arch(self, arch):
        # build_arch runs after the source archive has been unpacked.
        self._patch_cython_sprite_source(arch)
        return super().build_arch(arch)


recipe = Pygame261Recipe()
