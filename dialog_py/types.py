import ctypes

from .helpers import native_bridge, extended_named_tuple, Any
from .native import Vars, State as NativeState, Color


class Variables(metaclass=native_bridge):
    def __init__(self, lib):
        self._o = Vars.in_dll(lib, 'dialog_vars')

    beep_after_signal = bool
    beep_signal = bool
    begin_set = bool
    cant_kill = bool
    colors = bool
    cr_wrap = bool
    defaultno = bool
    dlg_clear_screen = bool
    extra_button = bool
    help_button = bool
    help_status = bool
    input_menu = bool
    insecure = bool
    item_help = bool
    keep_window = bool
    nocancel = bool
    nocollapse = bool
    print_siz = bool
    separate_output = bool
    single_quoted = bool
    size_err = bool
    tab_correct = bool
    trim_whitespace = bool
    keep_tite = bool
    ascii_lines = bool
    no_lines = bool
    nook = bool
    quoted = bool
    in_helpfile = bool
    no_nl_expand = bool
    no_tags = bool
    no_items = bool
    last_key = bool
    help_tags = bool
    iso_week = bool
    reorder = bool

    begin_x = int
    begin_y = int
    max_input = int
    scale_factor = int
    sleep_secs = int
    timeout_secs = int
    input_length = int
    formitem_type = int
    default_button = int

    backtitle = str
    cancel_label = str
    default_item = str
    exit_label = str
    extra_label = str
    help_label = str
    input_result = str
    no_label = str
    ok_label = str
    title = str
    yes_label = str
    column_header = str
    column_separator = str
    output_separator = str
    date_format = str
    time_format = str
    help_line = str
    help_file = str
    week_start = str


class State(metaclass=native_bridge):
    def __init__(self, lib):
        self._o = NativeState.in_dll(lib, 'dialog_state')

    screen_initialized = bool
    use_colors = bool
    use_scrollbar = bool
    use_shadow = bool
    visit_items = bool
    no_mouse = bool
    finish_string = bool
    plain_buttons = bool

    aspect_ratio = int
    output_count = int
    tab_len = int
    visit_cols = int

    output = Any
    pipe_input = Any
    screen_output = Any
    input = Any
    trace_output = Any

    separate_str = str


class ColorBinding(metaclass=native_bridge):
    def __init__(self, table, index):
        self._o = table[index]

    atr = int
    fg = int
    bg = int
    hilite = int
    name = str
    comment = str


class ColorList:
    def __init__(self, lib):
        self._lib = ctypes.POINTER(Color).in_dll(lib, 'dlg_color_table')
        self._size = None

    def __getitem__(self, key):
        return ColorBinding(self._lib, int(key))

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __len__(self):
        if self._size is None:
            self._size = self._lib.dlg_color_count()
        return self._size

    def __repr__(self):
        return '(%s)' % ', '.join((repr(i) for i in self))


class DLLWithHeader(ctypes.CDLL):
    def __init__(self, name, header, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self._header = header

    def __getitem__(self, item):
        v = super().__getitem__(item)
        types = self._header.get(item)
        if types is not None:
            v.restype = types[0]
            v.argtypes = types[1:]
        return v


ListItem = extended_named_tuple('ListItem', {'name': str, 'text': str, 'help': str, 'state': int})
FormItem = extended_named_tuple('FormItem', {'type': bool, 'name': str, 'name_len': int, 'name_y': int, 'name_x': int,
                                             'text': str, 'text_len': int, 'text_y': int, 'text_x': int,
                                             'text_flen': int, 'text_ilen': int, 'help': str})
