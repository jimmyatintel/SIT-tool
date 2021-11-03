import logging

from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

class ImageLabel(ttk.Label):
    """
    A class for handling images on the tool, such as a banner or icons.
    """
    def __init__(self, parent, file, alpha=True, background="#ffffff"):
        style_name = "{}.TLabel".format(id(file))
        banner_style = ttk.Style()
        banner_style.configure(style_name, foreground="white", background=background)
        super().__init__(parent, padding=-2, style=style_name) 
        # setting padding to -3 removes the excessive border!

        self.parent = parent

        self.image = Image.open(file).convert("RGBA") if alpha else Image.open(file)
        self.image_base = self.image.copy()
        self.photo = ImageTk.PhotoImage(self.image)
        self.configure(image=self.photo)
        
    def resize(self, size):
        new_width, new_height = size
        self.image = self.image_base.resize((new_width, new_height), Image.ANTIALIAS)
        self.photo = ImageTk.PhotoImage(self.image)
        self.config(image=self.photo)

    def dynamic_resize(self,event):
        """bind to resize event of window to make it work."""
        self.resize((event.width-4, event.height-4))

class CopyrightLabel(ttk.Label):
    """
    A class for handling copyright label on the tool
    """
    def __init__(self, parent, rows, columns):
        logging.info('Adding Intel label...')
        super().__init__(parent, text="Intel Corporation 2020", justify="right")
        self.grid(padx=5, pady=0, row=rows-1, column=columns - 2, columnspan=2, sticky="se")

class ToolTip(object):
    """
    A class for handling tips/information on a given widget.
    """
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 30
        y = y + cy + self.widget.winfo_rooty() + 30
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        try:
            # For Mac OS
            tw.tk.call("::tk::unsupported::MacWindowStyle",
                       "style", tw._w,
                       "help", "noActivates")
        except tk.TclError:
            pass
        label = tk.Label(tw, text=self.text, justify="left",
                      background="#ffffe0", relief="solid", borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def createToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

class Dialog(tk.Toplevel):

    def __init__(self, parent, title = None, **body_args):

        super().__init__(parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = ttk.Frame(self)
        self.initial_focus = self.body(body, **body_args)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()

        self.wait_window(self)

    #
    # construction hooks

    def body(self, master, **body_args):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden

        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = ttk.Frame(self)

        w = ttk.Button(box, text="OK", width=10, command=self.ok, default="active")#ACTIVE)
        w.pack(side="left", padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side="left", padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    #
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):

        return 1 # override

    def apply(self):

        pass # override


class FilterDialog(Dialog):

    def body(self, master, options, precheck=[], icon=None, rows=4):
        if icon:
            self.iconbitmap(icon) 
        self.vars = []        
        for i,t in enumerate(options):
            box = ttk.Checkbutton(master, text=t)
            # box.state(['!alternate', '!selected', '!disabled'])
            box.text = t
            box.state(['!alternate', 'selected' if t in precheck else '!selected', '!disabled'])
            box.grid(padx=5, pady=5, row=i%rows, column=i//rows, sticky="nswe")
            self.vars.append(box)

        #     selection = ttk.Checkbutton(frame, text=t)
        # selection.text = t
        # selection.state(['!alternate', '!selected', '!disabled'])
        # selection.grid(padx=5, pady=5, row=1, column=0, sticky="nswe")
        return self.vars[0] # initial focus

    def apply(self):
        """ returns list of filtered out values """
        show = []
        hide = []
        for box in self.vars:
            if box.instate(['selected']):
                show.append(box.text)
            else:
                hide.append(box.text)
        # show is useless, because might overlap with "hide" tags
        self.result = hide

    def validate(self):
        return 1