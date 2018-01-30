class DialogError(Exception):
    pass


class Aborted(DialogError):
    def __init__(self, is_esc):
        self._is_esc = bool(is_esc)

    @property
    def is_esc(self):
        return self._is_esc


class NeedHelp(DialogError):
    pass


class NeedExtra(DialogError):
    pass


class DialogNotFoundError(DialogError):
    def __init__(self):
        super().__init__("Cannot find libdialog.so. Make sure that:\n  1) First argument of Dialog() valid library path"
                         " or None\n  2) cdialog installed on your computer\n  3) cdialog built with option "
                         "`--with-shared'\nYou can download cdialog source from `http://invisible-island.net/dialog/"
                         "dialog.html' and build it manually")
