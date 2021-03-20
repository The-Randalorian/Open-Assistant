#!/usr/bin/env python3

import os
import threading
from tkinter import Tk, Button, PhotoImage
import logging

from ... import plugins

core = plugins.services["core"][0]
stt = plugins.services["stt"][0]

_logger = logging.getLogger(f"{__name__}")

run_thread: threading.Thread
thread_active = False


@core.setup_task
def start_thread():
    global run_thread, thread_active
    thread_active = True
    run_thread = threading.Thread(target=thread_script)
    run_thread.start()


@core.cleanup_task
def close_thread():
    global run_thread, thread_active
    thread_active = False
    run_thread.join()


def thread_script():
    global thread_active, stt
    # print(threadActive)
    root = Tk("OpenAssistant Trigger")
    root.overrideredirect(1)
    root.config(bg="#151515")

    def callback():
        rt = threading.Thread(target=stt.trigger())
        rt.start()

    b = Button(root, text="Trigger", command=callback, bg="#151515", fg="#3DB8B8")
    photo = PhotoImage(file="apples/plugins/tkinter_trigger/logo.png")
    b.config(image=photo, width="200", height="200")
    b.pack()
    if os.name == 'nt':
        root.wm_attributes("-topmost", 1)
    # root.mainloop()
    while thread_active:
        root.update()
    root.destroy()
    thread_active = False
