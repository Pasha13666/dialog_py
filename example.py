#!/usr/bin/env python3

import sys
import time

import dialog_py

FAST_DEMO = False


def infobox_demo(d):
    d.dialog_msgbox("Demo", "Preparing demo, please wait...", 0, 0, False)

    if FAST_DEMO:
        time.sleep(0.5)
    else:
        time.sleep(3)


def gauge_demo(d):
    def gauge_object():
        for i in range(1, 101):
            yield i
            if FAST_DEMO:
                time.sleep(0.01)
            else:
                time.sleep(0.1)

    d.show_gauge("Preparing demo...", "", gauge_object())


def yesno_demo(d):
    try:
        d.dialog_yesno("Demo", "Do you like this demo?", 0, 0)
        return True
    except dialog_py.Aborted:
        return False


def msgbox_demo(d, answer):
    if answer:
        d.dialog_msgbox("Demo", "Press OK to see the source code.", 0, 0, True)
    else:
        d.dialog_msgbox("Demo", "Press OK to run `rm -rf /'.", 0, 0, True)


def textbox_demo(d):
    d.dialog_textbox("Demo", __file__, 0, 76)


def inputbox_demo(d):
    while True:
        try:
            d.dialog_inputbox("Demo", "What's your name?", 0, 0, "Pasha__kun", False)
            break
        except dialog_py.Aborted:
            pass


def menu_demo(d):
    while True:
        try:
            r = d.show_menu("Demo", "What's your favorite day of the week?",
                            dialog_py.ListItem("Monday", "Bad choice", "", 0),
                            dialog_py.ListItem("Tuesday", "Hmm", "", 0),
                            dialog_py.ListItem("Wednesday", "", "", 0),
                            dialog_py.ListItem("Thursday", "Before Friday", "", 0),
                            dialog_py.ListItem("Friday", "The best day", "", 0),
                            dialog_py.ListItem("Saturday", "You can code at home", "", 0),
                            dialog_py.ListItem("Sunday", "You can code at home again", "", 0),
                            width=60)
            break
        except dialog_py.Aborted:
            pass

    return r


def checklist_demo(d):
    while True:
        try:
            curr, sel = d.show_checklist("Demo", "What features of `dialog' will you use?",
                                         dialog_py.ListItem("checklist", "This demo", "", 0),
                                         dialog_py.ListItem("menu", "Previous demo", "", 0),
                                         dialog_py.ListItem("radiolist", "Next demo", "", 0),
                                         dialog_py.ListItem("gauge", "", "Progress bar", 0),
                                         dialog_py.ListItem("yesno", "Simple question", "", 0),
                                         dialog_py.ListItem("fselect", "Choose file", "", 0),
                                         height=15, width=54, list_height=7, multi_select=True,
                                         states=[False, False, False, True, True, True])
            break
        except dialog_py.Aborted:
            pass

    if 5 in sel:
        d.dialog_msgbox("Demo", "Is is bad idea. This version of dialog_py doesn't support fselect", 0, 0, True)


def radiolist_demo(d):
    while True:
        try:
            curr, sel = d.show_checklist("Demo", "I am too lazy to make demos for all methods",
                                         dialog_py.ListItem("Pff", "9 demo is a lot", "", 0),
                                         dialog_py.ListItem("...", "I am too lazy to watch it", "", 0),
                                         dialog_py.ListItem("Fffuuu", "How to close this??", "", 0),
                                         dialog_py.ListItem("^-", "Hey! Press <enter>", "", 0),
                                         dialog_py.ListItem("^-", "Thank U, bro!", "", 0),
                                         width=65)
            break
        except dialog_py.Aborted:
            pass
    return sel


def demo():
    with dialog_py.Dialog() as d:
        infobox_demo(d)
        gauge_demo(d)
        answer = yesno_demo(d)
        msgbox_demo(d, answer)
        textbox_demo(d)
        inputbox_demo(d)
        menu_demo(d)
        checklist_demo(d)
        radiolist_demo(d)


def main():
    try:
        demo()
    except (dialog_py.DialogError, OSError):
        sys.stderr.write("Error!")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
