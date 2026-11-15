"""Android üçün PyCreator layihə yaddaşı və icazə idarəetməsi."""
import os
import shutil


class StorageManager:
    PROMPT_MARKER = ".storage_permission_prompted"

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.prompt_marker = os.path.join(data_dir, self.PROMPT_MARKER)

    def _android(self):
        try:
            from jnius import autoclass
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            return activity, autoclass
        except Exception:
            return None, None

    def public_projects_dir(self):
        activity, autoclass = self._android()
        if activity is None:
            return None
        try:
            env = autoclass("android.os.Environment")
            root = env.getExternalStorageDirectory().getAbsolutePath()
            return os.path.join(root, "Download", "PyProjects")
        except Exception:
            return None

    def has_access(self):
        activity, autoclass = self._android()
        if activity is None:
            return False
        try:
            Build = autoclass("android.os.Build")
            if Build.VERSION.SDK_INT >= 30:
                env = autoclass("android.os.Environment")
                return bool(env.isExternalStorageManager())
            PackageManager = autoclass("android.content.pm.PackageManager")
            read_ok = activity.checkSelfPermission(
                "android.permission.READ_EXTERNAL_STORAGE") == PackageManager.PERMISSION_GRANTED
            write_ok = activity.checkSelfPermission(
                "android.permission.WRITE_EXTERNAL_STORAGE") == PackageManager.PERMISSION_GRANTED
            return bool(read_ok and write_ok)
        except Exception:
            return False

    def request_access(self):
        """Android versiyasına uyğun sistem icazə ekranını açır."""
        activity, autoclass = self._android()
        if activity is None:
            return False
        try:
            Build = autoclass("android.os.Build")
            if Build.VERSION.SDK_INT >= 30:
                Intent = autoclass("android.content.Intent")
                Settings = autoclass("android.provider.Settings")
                Uri = autoclass("android.net.Uri")
                package_uri = Uri.parse("package:" + activity.getPackageName())
                intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                intent.setData(package_uri)
                try:
                    activity.startActivity(intent)
                except Exception:
                    # Bəzi Android ROM-larında tətbiqə aid action mövcud olmur.
                    fallback = Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION)
                    activity.startActivity(fallback)
            else:
                # python-for-android-ın rəsmi runtime permission API-si.
                from android.permissions import request_permissions
                request_permissions([
                    "android.permission.READ_EXTERNAL_STORAGE",
                    "android.permission.WRITE_EXTERNAL_STORAGE",
                ])
            return True
        except Exception:
            return False

    def request_on_first_launch(self):
        """İlk Android açılışında bir dəfə icazə sorğusu göndərir."""
        if self._android()[0] is None:
            return False
        if self.has_access():
            self._mark_prompted()
            return False
        if os.path.exists(self.prompt_marker):
            return False
        if self.request_access():
            # İstifadəçi icazəni rədd etsə belə hər açılışda narahat edilmir.
            self._mark_prompted()
            return True
        return False

    def _mark_prompted(self):
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.prompt_marker, "w", encoding="utf-8") as marker:
                marker.write("1")
        except OSError:
            pass

    def prepare(self, old_dir=None):
        """İcazə varsa Download/PyProjects, yoxdursa tətbiqin daxili yaddaşı."""
        public_dir = self.public_projects_dir()
        if public_dir and self.has_access():
            try:
                os.makedirs(public_dir, exist_ok=True)
                if old_dir and os.path.realpath(old_dir) != os.path.realpath(public_dir):
                    self._migrate(old_dir, public_dir)
                return public_dir, True
            except OSError:
                pass
        fallback = os.path.join(self.data_dir, "PyProjects")
        os.makedirs(fallback, exist_ok=True)
        if old_dir and os.path.realpath(old_dir) != os.path.realpath(fallback):
            self._migrate(old_dir, fallback)
        return fallback, False

    @staticmethod
    def _migrate(source, destination):
        if not source or not os.path.isdir(source):
            return
        for root, dirs, files in os.walk(source):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            relative = os.path.relpath(root, source)
            target = destination if relative == "." else os.path.join(destination, relative)
            os.makedirs(target, exist_ok=True)
            for filename in files:
                if filename.startswith("."):
                    continue
                src = os.path.join(root, filename)
                dst = os.path.join(target, filename)
                if not os.path.exists(dst):
                    try:
                        shutil.copy2(src, dst)
                    except OSError:
                        pass
