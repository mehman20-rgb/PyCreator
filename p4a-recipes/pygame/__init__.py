"""Android-compatible Pygame recipe for CPython 3.14.

Pygame 2.6.1's optional Cython _sprite extension fails with Cython 3.1
because of an obsolete __dict__ assignment. The normal pygame.sprite module
is pure Python and remains available; omit only this optional accelerator.
"""
from pathlib import Path

from pythonforandroid.recipes.pygame import Pygame2Recipe


class Pygame261Recipe(Pygame2Recipe):
    version = "2.6.1"
    url = "https://github.com/pygame/pygame/archive/{version}.tar.gz"
    hostpython_prerequisites = ["setuptools", "cython>=3.1"]

    def _patch_optional_sprite_accelerator(self, arch):
        build_dir = Path(self.get_build_dir(arch.arch))

        # This extension is optional; pygame.sprite continues to work in Python.
        sprite_source = (
            build_dir / "src_c" / "cython" / "pygame" / "_sprite.pyx"
        )
        if sprite_source.exists():
            sprite_source.unlink()

        generated_sprite = build_dir / "src_c" / "_sprite.c"
        if generated_sprite.exists():
            generated_sprite.unlink()

        android_setup = build_dir / "buildconfig" / "Setup.Android.SDL2.in"
        if android_setup.exists():
            content = android_setup.read_text(encoding="utf-8")
            content = "\\n".join(
                line for line in content.splitlines()
                if not line.lstrip().startswith("_sprite ")
            ) + "\\n"
            android_setup.write_text(content, encoding="utf-8")

    def build_arch(self, arch):
        # Run after the source archive is unpacked, immediately before setup.py.
        self._patch_optional_sprite_accelerator(arch)
        return super().build_arch(arch)


recipe = Pygame261Recipe()
