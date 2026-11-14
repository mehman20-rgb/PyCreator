"""Pure-Python Android recipe for charset-normalizer.

python-for-android may discover an Android-specific prebuilt wheel for this
package, then attempt to install that wheel with the host pip interpreter.
That fails because the host interpreter does not accept Android wheel tags.
Build the upstream source instead.  MypyC is deliberately disabled, so the
package stays pure Python and needs no native extension.
"""
from pythonforandroid.recipe import PyProjectRecipe


class CharsetNormalizerRecipe(PyProjectRecipe):
    version = "3.4.4"
    url = "https://github.com/jawah/charset_normalizer/archive/refs/tags/{version}.tar.gz"

    def check_prebuilt(self, arch, msg=""):
        # Do not select cp314-android_* wheels for the host-side installer.
        return False

    def get_recipe_env(self, arch, **kwargs):
        env = super().get_recipe_env(arch, **kwargs)
        env["CHARSET_NORMALIZER_USE_MYPYC"] = "0"
        return env


recipe = CharsetNormalizerRecipe()
