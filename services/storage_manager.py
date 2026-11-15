"""PyCreator üçün daxili test faylları və Android sənəd seçicisi."""
import os
import shutil


class StorageManager:
    """Test fayllarını daxildə saxlayır, istifadəçi fayllarını SAF ilə ixrac edir."""

    CREATE_DOCUMENT_REQUEST = 4817

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.test_dir = os.path.join(data_dir, "TestFiles")
        self._save_callback = None
        self._activity_module = None
        self._pending_filename = None

    def _android(self):
        try:
            from jnius import autoclass
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            return activity, autoclass
        except Exception:
            return None, None

    def has_access(self):
        # SAF hər fayl üçün istifadəçinin seçdiyi URI-yə giriş verir.
        return False

    def public_projects_dir(self):
        # Artıq ümumi yaddaşa birbaşa yol istifadə edilmir.
        return None

    def prepare(self, old_dir=None):
        """Daxildə yalnız nümunə/test faylları üçün qovluq yaradır."""
        os.makedirs(self.test_dir, exist_ok=True)
        if old_dir and os.path.realpath(old_dir) != os.path.realpath(self.test_dir):
            self._migrate(old_dir, self.test_dir)
        return self.test_dir, False

    def create_document(self, content, filename, callback):
        """Android fayl seçicisini açır və seçilmiş sənədə UTF-8 mətn yazır."""
        activity, autoclass = self._android()
        if activity is None:
            callback(False, "Android fayl seçicisi yalnız Android-də mövcuddur.")
            return False
        try:
            from android import activity as android_activity
            Intent = autoclass("android.content.Intent")
            intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            # Python mənbə faylıdır; text/plain bəzi file provider-lərdə .txt əlavə edir.
            intent.setType("text/x-python")
            intent.putExtra(Intent.EXTRA_TITLE, filename or "untitled.py")
            intent.addFlags(
                Intent.FLAG_GRANT_READ_URI_PERMISSION |
                Intent.FLAG_GRANT_WRITE_URI_PERMISSION |
                Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)

            self._save_callback = callback
            self._pending_content = content
            self._pending_filename = filename or "untitled.py"
            self._activity_module = android_activity
            android_activity.bind(on_activity_result=self._on_activity_result)
            activity.startActivityForResult(intent, self.CREATE_DOCUMENT_REQUEST)
            return True
        except Exception as exc:
            self._unbind_result()
            self._save_callback = None
            callback(False, str(exc))
            return False

    def _on_activity_result(self, request_code, result_code, intent):
        if request_code != self.CREATE_DOCUMENT_REQUEST:
            return
        callback = self._save_callback
        self._save_callback = None
        try:
            from jnius import autoclass
            Activity = autoclass("android.app.Activity")
            Intent = autoclass("android.content.Intent")
            if result_code != Activity.RESULT_OK or intent is None:
                if callback:
                    callback(False, "Saxlama ləğv edildi.")
                return
            uri = intent.getData()
            if uri is None:
                if callback:
                    callback(False, "Android fayl ünvanı qaytarmadı.")
                return
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()
            uri_string = str(uri.toString())
            if not uri_string.startswith("content://"):
                raise ValueError("Android fayl seçicisi etibarlı content:// URI qaytarmadı.")

            # SAF icazəsini mümkün olduqda tətbiqin növbəti açılışları üçün saxla.
            try:
                flags = intent.getFlags()
                grant_flags = flags & (
                    Intent.FLAG_GRANT_READ_URI_PERMISSION |
                    Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                if (grant_flags and
                        flags & Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION):
                    resolver.takePersistableUriPermission(uri, grant_flags)
            except Exception:
                # Bəzi DocumentsProvider-lər persistable grant vermir;
                # cari sessiyada yazmaq yenə də mümkün ola bilər.
                pass

            # Provider MIME tipinə görə .txt əlavə edibsə, mümkün olduqda
            # seçilmiş .py adını DocumentsContract vasitəsilə bərpa et.
            try:
                DocumentsContract = autoclass("android.provider.DocumentsContract")
                renamed_uri = DocumentsContract.renameDocument(
                    resolver, uri, self._pending_filename)
                if renamed_uri is not None:
                    uri = renamed_uri
                    uri_string = str(uri.toString())
            except Exception:
                # Bəzi provider-lər rename dəstəkləmir; MIME + EXTRA_TITLE qalır.
                pass

            stream = resolver.openOutputStream(uri, "wt")
            if stream is None:
                raise IOError("Faylı yazmaq üçün axın açıla bilmədi.")
            Writer = autoclass("java.io.OutputStreamWriter")
            writer = Writer(stream, "UTF-8")
            try:
                writer.write(self._pending_content)
                writer.flush()
            finally:
                writer.close()
            if callback:
                # str(uri) PyJNIus-da Java obyektinin LocalRef təsvirini verə bilər.
                # toString() isə content://... URI mətnini qaytarır.
                callback(True, uri_string)
        except Exception as exc:
            if callback:
                callback(False, str(exc))
        finally:
            self._pending_content = None
            self._pending_filename = None
            self._unbind_result()

    def write_document(self, uri_string, content, callback):
        """Əvvəl seçilmiş sənəd URI-sinə yenidən yazır."""
        try:
            activity, autoclass = self._android()
            if activity is None:
                raise RuntimeError("Android sənəd xidməti əlçatan deyil.")
            uri_string = str(uri_string or "").strip()
            if not uri_string.startswith("content://"):
                raise ValueError("Saxlanmış fayl ünvanı etibarsızdır; yenidən Save As edin.")
            Uri = autoclass("android.net.Uri")
            Writer = autoclass("java.io.OutputStreamWriter")
            uri = Uri.parse(uri_string)
            if uri is None or str(uri.getScheme()) != "content":
                raise ValueError("Saxlanmış Android content URI açıla bilmədi.")
            stream = activity.getContentResolver().openOutputStream(uri, "wt")
            if stream is None:
                raise IOError("Sənəd yazmaq üçün açıla bilmədi.")
            writer = Writer(stream, "UTF-8")
            try:
                writer.write(content)
                writer.flush()
            finally:
                writer.close()
            callback(True, uri_string)
        except Exception as exc:
            callback(False, str(exc))

    def _unbind_result(self):
        if self._activity_module is not None:
            try:
                self._activity_module.unbind(on_activity_result=self._on_activity_result)
            except Exception:
                pass
            self._activity_module = None

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
