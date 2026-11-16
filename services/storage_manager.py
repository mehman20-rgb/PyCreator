"""PyCreator üçün Android SAF qovluq icazəsi və Download/pyProject saxlama sistemi."""
import os
import shutil


class StorageManager:
    """İlk Save zamanı Download qovluğuna SAF icazəsi alır və pyProject yaradır."""

    TREE_REQUEST = 4817
    TREE_URI_FILE = ".storage_tree_uri"
    PROJECT_URI_FILE = ".project_dir_uri"

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.test_dir = os.path.join(data_dir, "TestFiles")
        self._save_callback = None
        self._activity_module = None
        self._pending_filename = None
        self._pending_content = None
        self._tree_uri = None
        self._project_uri = None
        self._load_saved_uris()

    def _android(self):
        try:
            from jnius import autoclass
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            return activity, autoclass
        except Exception:
            return None, None

    def _load_saved_uris(self):
        for attr, filename in (
            ("_tree_uri", self.TREE_URI_FILE),
            ("_project_uri", self.PROJECT_URI_FILE),
        ):
            try:
                with open(os.path.join(self.data_dir, filename), encoding="utf-8") as stream:
                    value = stream.read().strip()
                setattr(self, attr, value if value.startswith("content://") else None)
            except OSError:
                setattr(self, attr, None)

    def _save_uri(self, filename, value):
        os.makedirs(self.data_dir, exist_ok=True)
        path = os.path.join(self.data_dir, filename)
        temporary = path + ".tmp"
        with open(temporary, "w", encoding="utf-8") as stream:
            stream.write(value or "")
        os.replace(temporary, path)

    def has_access(self):
        return bool(self._tree_uri and self._project_uri)

    def public_projects_dir(self):
        # SAF URI-si POSIX fayl yolu deyil; public path kimi qaytarılmır.
        return self._project_uri

    def prepare(self, old_dir=None):
        """Daxili test fayllarını saxlayır; istifadəçi faylları SAF qovluğuna yazılır."""
        os.makedirs(self.test_dir, exist_ok=True)
        if old_dir and os.path.realpath(old_dir) != os.path.realpath(self.test_dir):
            self._migrate(old_dir, self.test_dir)
        return self.test_dir, False

    def create_document(self, content, filename, callback):
        """Faylı əvvəlcədən icazə verilmiş pyProject qovluğuna yaradır."""
        self._save_callback = callback
        self._pending_content = content
        self._pending_filename = self._safe_python_name(filename)

        if self._project_uri:
            try:
                self._create_file_in_project()
                return True
            except Exception as exc:
                # Saxlanmış tree icazəsi ləğv edilibsə, yenidən qovluq seçdir.
                self._tree_uri = None
                self._project_uri = None
                self._save_uri(self.TREE_URI_FILE, "")
                self._save_uri(self.PROJECT_URI_FILE, "")

        return self._request_project_folder()

    @staticmethod
    def _safe_python_name(filename):
        name = os.path.basename((filename or "untitled.py").replace("\\", "/")).strip()
        if not name:
            name = "untitled.py"
        base, extension = os.path.splitext(name)
        if extension.lower() != ".py":
            name = (base if extension else name) + ".py"
        return name

    def _request_project_folder(self):
        activity, autoclass = self._android()
        if activity is None:
            self._finish(False, "Android qovluq seçicisi yalnız Android-də mövcuddur.")
            return False
        try:
            from android import activity as android_activity
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            DocumentsContract = autoclass("android.provider.DocumentsContract")

            intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
            intent.addFlags(
                Intent.FLAG_GRANT_READ_URI_PERMISSION |
                Intent.FLAG_GRANT_WRITE_URI_PERMISSION |
                Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)

            # Picker mümkün olduqda birbaşa Download qovluğunda açılsın.
            try:
                initial = Uri.parse(
                    "content://com.android.externalstorage.documents/document/primary%3ADownload")
                intent.putExtra(DocumentsContract.EXTRA_INITIAL_URI, initial)
            except Exception:
                pass

            self._activity_module = android_activity
            android_activity.bind(on_activity_result=self._on_activity_result)
            activity.startActivityForResult(intent, self.TREE_REQUEST)
            return True
        except Exception as exc:
            self._unbind_result()
            self._finish(False, "Yaddaş qovluğu seçicisi açıla bilmədi: %s" % exc)
            return False

    def _on_activity_result(self, request_code, result_code, intent):
        if request_code != self.TREE_REQUEST:
            return
        try:
            from jnius import autoclass
            Activity = autoclass("android.app.Activity")
            Intent = autoclass("android.content.Intent")
            if result_code != Activity.RESULT_OK or intent is None:
                self._finish(False, "Qovluq seçimi ləğv edildi.")
                return

            tree_uri = intent.getData()
            if tree_uri is None:
                raise IOError("Android etibarlı qovluq ünvanı qaytarmadı.")

            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            resolver = activity.getContentResolver()
            flags = intent.getFlags()
            grant_flags = flags & (
                Intent.FLAG_GRANT_READ_URI_PERMISSION |
                Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            if not grant_flags:
                grant_flags = (Intent.FLAG_GRANT_READ_URI_PERMISSION |
                               Intent.FLAG_GRANT_WRITE_URI_PERMISSION)

            # Qovluq icazəsini tətbiqin növbəti açılışları üçün saxla.
            resolver.takePersistableUriPermission(tree_uri, grant_flags)
            self._tree_uri = str(tree_uri.toString())
            self._project_uri = self._find_or_create_project_folder(
                resolver, tree_uri, autoclass)
            self._save_uri(self.TREE_URI_FILE, self._tree_uri)
            self._save_uri(self.PROJECT_URI_FILE, self._project_uri)
            self._create_file_in_project()
        except Exception as exc:
            self._finish(False, "pyProject qovluğu yaradıla bilmədi: %s" % exc)
        finally:
            self._unbind_result()

    def _find_or_create_project_folder(self, resolver, tree_uri, autoclass):
        DocumentsContract = autoclass("android.provider.DocumentsContract")
        Document = autoclass("android.provider.DocumentsContract$Document")
        Uri = autoclass("android.net.Uri")
        tree_document_id = DocumentsContract.getTreeDocumentId(tree_uri)
        parent_uri = DocumentsContract.buildDocumentUriUsingTree(
            tree_uri, tree_document_id)
        children_uri = DocumentsContract.buildChildDocumentsUriUsingTree(
            tree_uri, tree_document_id)

        cursor = None
        try:
            cursor = resolver.query(
                children_uri,
                [Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME,
                 Document.COLUMN_MIME_TYPE],
                None, None, None)
            if cursor is not None:
                id_col = cursor.getColumnIndex(Document.COLUMN_DOCUMENT_ID)
                name_col = cursor.getColumnIndex(Document.COLUMN_DISPLAY_NAME)
                mime_col = cursor.getColumnIndex(Document.COLUMN_MIME_TYPE)
                while cursor.moveToNext():
                    name = cursor.getString(name_col)
                    mime = cursor.getString(mime_col)
                    if name == "pyProject" and mime == Document.MIME_TYPE_DIR:
                        doc_id = cursor.getString(id_col)
                        return str(DocumentsContract.buildDocumentUriUsingTree(
                            tree_uri, doc_id).toString())
        finally:
            if cursor is not None:
                cursor.close()

        folder_uri = DocumentsContract.createDocument(
            resolver, parent_uri, Document.MIME_TYPE_DIR, "pyProject")
        if folder_uri is None:
            raise IOError("Download daxilində pyProject qovluğu yaradıla bilmədi.")
        return str(folder_uri.toString())

    def _create_file_in_project(self):
        activity, autoclass = self._android()
        if activity is None:
            raise RuntimeError("Android sənəd xidməti əlçatan deyil.")
        if not self._project_uri or not self._project_uri.startswith("content://"):
            raise ValueError("pyProject qovluğunun icazəsi yoxdur.")

        Uri = autoclass("android.net.Uri")
        DocumentsContract = autoclass("android.provider.DocumentsContract")
        Document = autoclass("android.provider.DocumentsContract$Document")
        Writer = autoclass("java.io.OutputStreamWriter")
        resolver = activity.getContentResolver()
        folder_uri = Uri.parse(self._project_uri)

        file_uri = DocumentsContract.createDocument(
            resolver, folder_uri, "text/x-python", self._pending_filename)
        if file_uri is None:
            # Bəzi provider-lər text/x-python MIME tipini qəbul etmir.
            file_uri = DocumentsContract.createDocument(
                resolver, folder_uri, "application/octet-stream",
                self._pending_filename)
        if file_uri is None:
            raise IOError("Python faylı pyProject qovluğunda yaradıla bilmədi.")

        # Bəzi DocumentsProvider-lər MIME tipinə görə uzantını dəyişə bilər.
        # Fayl adını dəqiq .py saxlamaq üçün rename əməliyyatını yoxla.
        try:
            renamed_uri = DocumentsContract.renameDocument(
                resolver, file_uri, self._pending_filename)
            if renamed_uri is not None:
                file_uri = renamed_uri
        except Exception:
            pass

        uri_string = str(file_uri.toString())
        stream = resolver.openOutputStream(file_uri, "wt")
        if stream is None:
            raise IOError("Faylı yazmaq üçün Android axını açıla bilmədi.")
        writer = Writer(stream, "UTF-8")
        try:
            writer.write(self._pending_content or "")
            writer.flush()
        finally:
            writer.close()

        self._finish(True, uri_string)

    def write_document(self, uri_string, content, callback):
        """Əvvəl yaradılmış content:// sənədini yenidən yazır."""
        try:
            activity, autoclass = self._android()
            if activity is None:
                raise RuntimeError("Android sənəd xidməti əlçatan deyil.")
            uri_string = str(uri_string or "").strip()
            if not uri_string.startswith("content://"):
                raise ValueError("Saxlanmış fayl URI-si etibarsızdır.")
            Uri = autoclass("android.net.Uri")
            Writer = autoclass("java.io.OutputStreamWriter")
            uri = Uri.parse(uri_string)
            resolver = activity.getContentResolver()
            stream = resolver.openOutputStream(uri, "wt")
            if stream is None:
                raise IOError("Sənəd yazmaq üçün açıla bilmədi.")
            writer = Writer(stream, "UTF-8")
            try:
                writer.write(content)
                writer.flush()
            finally:
                writer.close()
            callback(True, str(uri.toString()))
        except Exception as exc:
            callback(False, str(exc))

    def _finish(self, ok, result):
        callback = self._save_callback
        self._save_callback = None
        self._pending_content = None
        self._pending_filename = None
        if callback:
            callback(ok, result)

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
