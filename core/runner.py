"""İstifadəçi kodunu ayrıca thread-də işlədir: çıxışı tutur, input() dəstəkləyir, Dayan düyməsi var."""
import builtins
import ctypes
import linecache
import sys
import threading
import time
import traceback


class _Router:
    """sys.stdout/stderr əvəzinə qoyulur: yalnız kod thread-indən gələn yazıları tutur."""

    def __init__(self, original, runner):
        self._orig = original
        self._runner = runner

    def write(self, text):
        if self._runner.is_worker():
            if text:
                self._runner.on_output(text)
            return len(text)
        return self._orig.write(text)

    def flush(self):
        if not self._runner.is_worker():
            try:
                self._orig.flush()
            except Exception:
                pass

    def isatty(self):
        return False

    def __getattr__(self, name):
        return getattr(self._orig, name)


class _StdinRouter:
    def __init__(self, original, runner):
        self._orig = original
        self._runner = runner

    def readline(self, *args):
        if self._runner.is_worker():
            return self._runner.ask("") + "\n"
        return self._orig.readline(*args)

    def __getattr__(self, name):
        return getattr(self._orig, name)


class Runner:
    def __init__(self, on_output, on_input, on_finish):
        """Bütün callback-lər işçi thread-dən çağırılır; UI özü thread-ə keçidi həll etməlidir.

        on_output(text)            kod nəsə çap etdikdə
        on_input(prompt)           kod input() çağırdıqda (UI yazı sahəsini göstərməlidir)
        on_finish(status, secs)    status: "ok" | "error" | "stopped"
        """
        self.on_output = on_output
        self.on_input = on_input
        self.on_finish = on_finish
        self._thread = None
        self._stop = False
        self._answer = None
        self._answer_ready = threading.Event()
        self._real_input = builtins.input
        if not isinstance(sys.stdout, _Router):
            sys.stdout = _Router(sys.stdout, self)
            sys.stderr = _Router(sys.stderr, self)
            sys.stdin = _StdinRouter(sys.stdin, self)
        builtins.input = self._input

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def is_worker(self):
        return self._thread is not None and threading.current_thread() is self._thread

    # ---------- input ----------
    def ask(self, prompt):
        if self._stop:
            raise KeyboardInterrupt
        self._answer = None
        self._answer_ready.clear()
        self.on_input(prompt)
        self._answer_ready.wait()
        if self._stop:
            raise KeyboardInterrupt
        text = self._answer or ""
        self.on_output(text + "\n")
        return text

    def _input(self, prompt=""):
        if not self.is_worker():
            return self._real_input(prompt)
        if prompt:
            self.on_output(str(prompt))
        return self.ask(str(prompt))

    def provide_input(self, text):
        self._answer = text
        self._answer_ready.set()

    # ---------- işə salma / dayandırma ----------
    def start(self, code, name="kod"):
        if self.running:
            return False
        self._stop = False
        self._answer_ready.clear()
        self._thread = threading.Thread(target=self._work, args=(code, name), daemon=True)
        self._thread.start()
        return True

    def stop(self):
        if not self.running:
            return
        self._stop = True
        self._answer_ready.set()
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_ulong(self._thread.ident), ctypes.py_object(KeyboardInterrupt))

    def _work(self, code, name):
        started = time.time()
        filename = "<%s-%d>" % (name, int(started * 1000))
        status = "ok"
        try:
            lines = code.splitlines(True)
            linecache.cache[filename] = (len(code), None, lines, filename)
            try:
                compiled = compile(code, filename, "exec")
            except SyntaxError as err:
                self.on_output("".join(traceback.format_exception_only(type(err), err)))
                status = "error"
            else:
                exec(compiled, {"__name__": "__main__", "__file__": name})
        except SystemExit as err:
            # İstifadəçi kodu fayl tapılmadıqda raise SystemExit etdikdə
            # terminal bunu uğurlu icra kimi yox, xəta kimi göstərsin.
            status = "error"
            code_value = getattr(err, "code", None)
            if code_value not in (None, 0):
                self.on_output("Proqram dayandırıldı (exit code: %s)\\n" % code_value)
        except KeyboardInterrupt:
            status = "stopped"
        except BaseException as err:
            tb = err.__traceback__.tb_next if err.__traceback__ else None
            self.on_output("".join(traceback.format_exception(type(err), err, tb)))
            status = "error"
        finally:
            linecache.cache.pop(filename, None)
            self._stop = False
            self.on_finish(status, time.time() - started)
