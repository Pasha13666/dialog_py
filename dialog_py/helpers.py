import ctypes
import functools

from .exceptions import Aborted, NeedHelp, NeedExtra
from .native import FUNCTIONS

Any = object()


def native_bridge(name: str, bases: tuple, dct: dict):
    dct2 = {}
    while dct:
        k, v = dct.popitem()
        if k.startswith('_') or (not isinstance(v, type) and v is not Any):
            dct2[k] = v
            continue

        if v is str:
            def _set(self, value, name=k):
                if value is None:
                    setattr(self._o, name, 0)
                    delattr(self, '_v_' + name)

                else:
                    value = ctypes.c_char_p(str(value).encode())
                    setattr(self, '_v_' + name, value)
                    setattr(self._o, name, value)

            def _get(self, typ=v, name=k):
                value = getattr(self._o, name)
                return None if not value else typ(value).decode()

            dct2[k] = property(_get, _set)

        elif v is bytearray:
            def _set(self, value, name=k):
                if value is None:
                    setattr(self._o, name, 0)
                    delattr(self, '_v_' + name)

                else:
                    value = ctypes.c_char_p(bytearray(value))
                    setattr(self, '_v_' + name, value)
                    setattr(self._o, name, value)

            def _get(self, name=k):
                value = getattr(self._o, name)
                return None if not value else bytearray(value)

            dct2[k] = property(_get, _set)

        elif v is bytes:
            def _set(self, value, name=k):
                if value is None:
                    setattr(self._o, name, 0)
                    delattr(self, '_v_' + name)

                else:
                    value = ctypes.c_char_p(bytes(value))
                    setattr(self, '_v_' + name, value)
                    setattr(self._o, name, value)

            def _get(self, name=k):
                value = getattr(self._o, name)
                return None if not value else bytes(value)

            dct2[k] = property(_get, _set)

        elif v is Any:
            dct2[k] = property(lambda self, name=k: getattr(self._o, name),
                               lambda self, value, name=k: setattr(self._o, name, value))

        else:
            dct2[k] = property(lambda self, typ=v, name=k: typ(getattr(self._o, name)),
                               lambda self, value, typ=v, name=k: setattr(self._o, name, typ(value)))

    return type(name, bases, dct2)


def _to_native(self, obj):
    # Member is not protected, this function is method of `self'
    # noinspection PyProtectedMember
    for i, (k, typ) in enumerate(type(self)._fields):
        if typ is str:
            setattr(obj, k, str(self[i]).encode())
        else:
            setattr(obj, k, typ(self[i]))


def _from_native(cls, obj):
    args = []
    # Member is not protected, this method is method of `cls'
    # noinspection PyProtectedMember
    for k, typ in cls._fields:
        if typ is str:
            args.append(bytes(getattr(obj, k)).decode())
        else:
            args.append(typ(getattr(obj, k)))

    return cls(*args)


def extended_named_tuple(name: str, fields: dict, module=None):
    dct = {
        '__name__': name,
        '__slots__': (),
        '_fields': tuple(fields.items()),
        'from_native': classmethod(_from_native),
        'to_native': _to_native
    }
    exec('def __new__(cls, {0}):\n    return tuple.__new__(cls, ({0}))'.format(', '.join(fields)), dct, dct)

    if module is not None:
        dct['__module__'] = module

    for i, (k, t) in enumerate(fields.items()):
        dct[k] = property(lambda self, index=i, typ=t: typ(self[index]))

    return type(name, (tuple,), dct)


def res_check(status, result=None):
    if status == 0:
        return None if result is None else result.value
    if status == 255:
        raise Aborted(True)
    if status < 0:
        raise OSError(-status)
    if status == 1:
        raise Aborted(False)
    if status == 2 or status == 4:
        raise NeedHelp()
    if status == 3:
        raise NeedExtra()


def wrap_input_menu(fn, items):
    def wrapper(_, current, new_text):
        r = fn(items, current.value)
        if isinstance(r, str):
            r = r.encode()
        if isinstance(r, (bytes, bytearray)):
            new_text[:] = r
            return 0
        return -1

    return wrapper


def to_native(obj, dst, name=None):
    """

    :param obj: Source object
    :param dst: Target object
    :param name: Field name in dst or None if dst is structure
    :return: Result (if name is None, None elsewhere)
    """
    if name is None:
        if hasattr(dst, '_type_'):
            typ = dst._type_

            if isinstance(typ, str):
                if typ == 'h':
                    typ = ctypes.c_short
                elif typ == 'H':
                    typ = ctypes.c_ushort
                elif typ == 'l':
                    typ = ctypes.c_long
                elif typ == 'L':
                    typ = ctypes.c_ulong
                elif typ == 'i':
                    typ = ctypes.c_int
                elif typ == 'L':
                    typ = ctypes.c_uint
                elif typ == 'f':
                    typ = ctypes.c_float
                elif typ == 'd':
                    typ = ctypes.c_double
                elif typ == 'g':
                    typ = ctypes.c_longdouble
                elif typ == 'q':
                    typ = ctypes.c_longlong
                elif typ == 'Q':
                    typ = ctypes.c_ulonglong
                elif typ == 'b':
                    typ = ctypes.c_byte
                elif typ == 'B':
                    typ = ctypes.c_ubyte
                elif typ == 'c':
                    typ = ctypes.c_char
                elif typ == '?':
                    typ = ctypes.c_bool
                elif typ == 'z':
                    typ = ctypes.c_char_p
        else:
            typ = dst

        if issubclass(typ, ctypes.Structure):
            for name, typ in type(dst)._fields_:
                to_native(getattr(obj, name), dst, name)

        elif issubclass(typ, ctypes.Array):
            for i, x in zip(range(len(dst)), obj):
                to_native(x, dst[i])

        elif hasattr(dst, 'contents') or issubclass(typ, ctypes.c_char_p):  # pointer
            if issubclass(typ, ctypes.c_char_p):
                typ = ctypes.c_char

            if not dst:
                try:
                    v = (typ * (len(obj) + 1))()
                except TypeError:
                    v = (typ * 1)()
                dst = ctypes.cast(v, ctypes.POINTER(typ))

            if hasattr(obj, '__iter__'):
                for i, x in enumerate(obj):
                    v = dst[i]
                    dst[i] = to_native(x, v if hasattr(v, '_type_') else typ)

                if typ == ctypes.c_char:
                    dst[len(obj)] = 0

            else:
                to_native(obj, dst, 'contents')

        elif isinstance(obj, bool):
            return typ(int(obj))

        elif isinstance(obj, str):
            return typ(obj.encode())

        else:
            return typ(obj)

        return dst

    v = getattr(dst, name, None)

    if isinstance(v, (ctypes.Structure, ctypes.Array)) or hasattr(v, 'contents'):  # pointer
        if not v:
            try:
                v = (v._type_ * len(v))()
            except TypeError:
                v = (v._type_ * 1)()
            setattr(dst, name, v)

        to_native(obj, v)

    elif v is not None:
        v = to_native(obj, v)
        setattr(dst, name, v)
    else:
        v = to_native(obj, getattr(dst._type_, name))
        setattr(dst, name, v)

    return getattr(dst, name)


def make_wrapper(fn):
    ft = FUNCTIONS[fn.__name__]

    @functools.wraps(fn)
    def wrapper(*args):
        r = fn(*(to_native(v, ft[i + 1]()) for i, v in enumerate(args)))
        if isinstance(r, (bytes, bytearray)):
            return r.decode()

        res_check(r)

    return wrapper
