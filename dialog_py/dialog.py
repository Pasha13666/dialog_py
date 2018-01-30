import ctypes
import os
import sys
import threading
from ctypes.util import find_library

from .exceptions import DialogNotFoundError
from .helpers import res_check, wrap_input_menu, make_wrapper
from .native import FUNCTIONS, LIBC_FUNCTIONS, ListItem, FormItem, input_menu as input_menu_type
from .types import Variables, State, ColorList, DLLWithHeader

_dialog = None

c_char_p_p = ctypes.POINTER(ctypes.c_char_p)


class Dialog:
    def __new__(cls, *args, **kwargs):
        global _dialog

        if _dialog is not None:
            raise RuntimeError("Cant create new instance of %s" % cls.__name__)
        v = super().__new__(cls)
        _dialog = v
        return v

    def __init__(self, path=None, inp=sys.stdin, out=sys.stderr):
        self._closable = False
        self._closed = False
        self._tid = id(threading.current_thread())

        if path is None:
            path = find_library('dialog')

        if not path:
            raise DialogNotFoundError()

        self._lib = DLLWithHeader(path, FUNCTIONS)
        self._libc = DLLWithHeader(None, LIBC_FUNCTIONS)

        self.variables = Variables(self._lib)
        self.state = State(self._lib)
        self.colors = ColorList(self._lib)

        inp.flush()
        out.flush()

        i = os.dup(inp.fileno())

        try:
            self._inp = self._libc.fdopen(i, b"r")
        except:
            os.close(i)
            raise

        i = os.dup(out.fileno())

        try:
            self._out = self._libc.fdopen(i, b"w")
        except:
            os.close(i)
            self._libc.fclose(self._inp)
            raise

        try:
            self._lib.init_dialog(self._inp, self._out)
        except:
            self._libc.fclose(self._inp)
            self._libc.fclose(self._out)
            raise

        self._version = None
        self._closable = True

    def _check_thread(self):
        if self._tid is not None and self._tid != id(threading.current_thread()):
            raise RuntimeError("Dialog object used in another thread")

    def __enter__(self):
        self._check_thread()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._check_thread()
        self.close()

    def __del__(self):
        self._tid = None
        self.close()

    def close(self):
        global _dialog
        self._check_thread()

        if not self._closable:
            if _dialog is self:
                _dialog = None

        elif not self._closed:
            self._lib.end_dialog()
            self._libc.fclose(self._inp)
            self._libc.fclose(self._out)
            self._closed = True
            if _dialog is self:
                _dialog = None

    @property
    def closed(self):
        self._check_thread()
        return self._closed

    @property
    def version(self):
        if self._version is None:
            self._version = self._lib.dialog_version().decode()
        return self._version

    def show_build_list(self, title, prompt, *items, height=0, width=0, list_height=0, states=None):
        self._check_thread()
        v = (ListItem * len(items))()
        for i, item in enumerate(items):
            item.to_native(v[i])

        if states is None:
            states = [False] * len(items)

        elif len(states) != len(items):
            raise ValueError("States count must be equal items count")

        states = b''.join(b'\1' if i else b'\0' for i in states)
        r = ctypes.c_int(-1)
        r = res_check(self._lib.dlg_buildlist(title.encode(), prompt.encode(), height, width, list_height,
                                              len(items), v, states, 0, ctypes.pointer(r)), r)

        return r, [i for i in range(len(items)) if v[i].state]

    def show_checklist(self, title, prompt, *items, height=0, width=0, list_height=0, states=None, multi_select=False):
        self._check_thread()
        v = (ListItem * len(items))()
        for i, item in enumerate(items):
            item.to_native(v[i])

        if states is None:
            states = [False] * len(items)

        elif not multi_select and isinstance(states, int):
            states = [False] * (states - 1) + [True] + [False] * (len(items) - states - 1)

        elif len(states) != len(items):
            raise ValueError("States count must be equal items count")

        states = b''.join(b'\1' if i else b'\0' for i in states)
        r = ctypes.c_int(-1)
        r = res_check(self._lib.dlg_checklist(title.encode(), prompt.encode(), height, width, list_height,
                                              len(items), v, states, 1 if multi_select else 0, ctypes.pointer(r)), r)
        if multi_select:
            return r, [i for i in range(len(items)) if v[i].state]

        for i in range(len(items)):
            if v[i].state:
                return r, i
        return r, -1

    def show_edit_box(self, title, *items, height=0, width=0):
        self._check_thread()
        v = ctypes.cast(self._libc.malloc(ctypes.sizeof(ctypes.c_char_p) * (len(items) + 1)), c_char_p_p)
        rows = ctypes.c_int(len(items))

        for i, item in enumerate(items):
            x = ctypes.cast(self._libc.malloc(ctypes.sizeof(ctypes.c_char) * (len(item) + 1)), ctypes.c_char_p)
            ctypes.memmove(x, item.encode(), len(item))
            ctypes.cast(x, ctypes.POINTER(ctypes.c_char))[len(item)] = b'\0'
            v[i] = x
        v[len(items)] = None

        try:
            res_check(self._lib.dlg_editbox(title.encode(), ctypes.pointer(v),
                                            ctypes.pointer(rows), height, width))

        except:
            for i in range(rows.value):
                if v[i] is None:
                    break

                self._libc.free(ctypes.cast(v, ctypes.POINTER(ctypes.c_void_p))[i])
            self._libc.free(ctypes.cast(v, ctypes.c_void_p))
            raise

        res = []

        for i in range(rows.value):
            if v[i] is None:
                break

            res.append(v[i].decode())
            self._libc.free(ctypes.cast(v, ctypes.POINTER(ctypes.c_void_p))[i])
        self._libc.free(ctypes.cast(v, ctypes.c_void_p))

        return res

    def show_form(self, title, prompt, *items, height=0, width=0, form_height=0):
        self._check_thread()
        v = (FormItem * len(items))()
        for i, item in enumerate(items):
            item.to_native(v[i])

        r = ctypes.c_int(-1)
        return res_check(self._lib.dlg_form(
            title.encode(), prompt.encode(), height, width, form_height, len(items), v, ctypes.pointer(r)), r)

    def show_menu(self, title, prompt, *items, height=0, width=0, form_height=0, input_menu=None):
        self._check_thread()
        v = (ListItem * len(items))()
        for i, item in enumerate(items):
            item.to_native(v[i])

        if input_menu is not None:
            input_menu = wrap_input_menu(input_menu, items)
        else:
            input_menu = 0

        r = ctypes.c_int(-1)
        return res_check(self._lib.dlg_menu(
            title.encode(), prompt.encode(), height, width, form_height, len(items), v, ctypes.pointer(r),
            input_menu_type(input_menu)), r)

    def show_progress_box(self, title, prompt, fd, *, height=0, width=0, pause=False):
        self._check_thread()

        fp = self._libc.fdopen(os.dup(fd if isinstance(fd, int) else fd.fileno()), b'r')

        try:
            res_check(self._lib.dlg_progressbox(title.encode(), prompt.encode(), height, width, 1 if pause else 0, fp))
        finally:
            self._libc.fclose(fp)

    def show_tree_view(self, title, prompt, *items, height=0, width=0, list_height=0, depths=None, states=None,
                       multi_select=False):
        self._check_thread()
        v = (ListItem * len(items))()
        for i, item in enumerate(items):
            item.to_native(v[i])

        if states is None:
            states = [False] * len(items)

        elif len(states) != len(items):
            raise ValueError("States count must be equal items count")

        if depths is None:
            depths = [0] * len(items)

        elif len(depths) != len(items):
            raise ValueError("Depths count must be equal items count")

        d = (ctypes.c_int * len(items))()
        for i, x in enumerate(depths):
            d[i] = x

        states = b''.join(b'\1' if i else b'\0' for i in states)
        r = ctypes.c_int(-1)
        r = res_check(self._lib.dlg_treeview(
            title.encode(), prompt.encode(), height, width, list_height, len(items), v, states, d,
            1 if multi_select else 0, ctypes.pointer(r)), r)

        if multi_select:
            return r, [i for i in range(len(items)) if v[i].state]

        for i in range(len(items)):
            if v[i].state:
                return r, i
        return r, -1

    def show_gauge(self, title, prompt, obj, *, height=0, width=0):
        title = title.encode()
        prompt = prompt.encode()

        g = self._lib.dlg_allocate_gauge(title, prompt, height, width, 0)
        if not g:
            raise OSError()

        try:
            for i in obj:
                self._lib.dlg_update_gauge(g, i)

        finally:
            self._lib.dlg_free_gauge(g)

    def create_rc(self, path=None):
        if path is None:
            path = os.path.join(os.path.expanduser('~'), '.dialogrc')

        self._lib.create_rc(path.encode() if isinstance(path, str) else path)

    def __getattr__(self, item):
        return make_wrapper(getattr(self._lib, item))
