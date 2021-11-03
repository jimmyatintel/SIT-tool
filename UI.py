# -*- coding: utf-8 -*-
import sys
import tkinter.font as tkFont

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename, askopenfilenames

import os
import math
import subprocess
import platform # cpuinfo
from PIL import Image, ImageTk
from os.path import join as pjoin
import datetime
import configparser
import shutil # for zipping
import logging
import psutil # for security

# source files
from tkhelper import ImageLabel, ToolTip, createToolTip, CopyrightLabel
from tracers import Traces
import uiconfig

# set the resource directory to: ./resource, relative to this file
resrc_path = pjoin(os.path.abspath(os.path.dirname(__file__)), "resource")
_codec = "utf8"

def get_date_time():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d-%H-%M")
    
def zipfolder(folder):
    logging.info(f"Zipping directory \"{folder}\"...")
    shutil.make_archive(folder, "zip", folder)
    
def execute(customer, queue, time=None, reset=False):
    r"""This is the main function for executing ingredients selected by the user.
    Args:
        customer (str): customer name, used for naming the output directory. 
        queue (list (dict)): list of ingredients pending execution.
        time (str): datetime string, used for naming the output directory. 
    """

    # determine trace directory, and initialize tracer
    time = time if time is not None else get_date_time()
    logdir = pjoin(os.getcwd(), "-".join([customer,"SoftwareIssueTracer",time])) if not reset else None
    tracer = Traces(logdir=logdir, resrc_path=resrc_path, codec=_codec)

    # reset registry keys
    if reset: 
        tracer.regclr()
        return 

    # execute all ingredients
    for x in queue:
        LogType = x["id"]
        try:
            if LogType == 1:
                tracer.usb()
            if LogType == 2:
                tracer.highloadingactivities()
            if LogType == 3:
                tracer.idle()
            if LogType == 4:
                tracer.acpi()
            if LogType == 5:
                tracer.unexpected_reset()
            if LogType == 6:
                tracer.marker()
                tracer.display()
            if LogType == 7:
                tracer.slp_s0_status()
            if LogType == 8:
                tracer.tbt()
            if LogType == 9:
                tracer.acpi2()
            if LogType == 10:                
                tracer.livedumpfile()
            if LogType == 12:
                tracer.rst()
            if LogType == 13:
                tracer.video_performance()
            if LogType == 14:
                update_config("Realtime BSOD", enable=True, logdir=logdir)
                tracer.realtimebsod()
            if LogType == 15:
                update_config("TBT (boot)", enable=True, logdir=logdir)
                tracer.tbt_boot()
            if LogType == 16:
                tracer.optane()
            if LogType == 17:
                update_config("ISST", enable=True, logdir=logdir)
                tracer.isst()
            if LogType == 18:
                update_config("I2C", enable=True, logdir=logdir)
                tracer.i2c(acpi=False)
            if LogType == 19:                
                tracer.sysinfo()
            if LogType == 20:
                update_config("I2C ACPI", enable=True, logdir=logdir)
                tracer.i2c(acpi=True)
            if LogType == 21:
                update_config("Boot Trace", enable=True, logdir=logdir)
                tracer.graphic_boot()
            if LogType == 22:
                update_config("Wiman Driver Log", enable=True, logdir=logdir)
                tracer.wiman()
            if LogType == 23:
                tracer.installer()
            if LogType == 24:
                tracer.lms()
            if LogType == 25:
                tracer.icls()
            if LogType == 26:
                update_config("DAL Driver Log", enable=True, logdir=logdir)
                tracer.dal()
            if LogType == 27:
                update_config("MEI Driver Yellow Bang", enable=True, logdir=logdir)
                tracer.csme_yellowbang(mode="Tee")
            if LogType == 28:
                update_config("SPD Driver Yellow Bang", enable=True, logdir=logdir)
                tracer.csme_yellowbang(mode="SPD")
            if LogType == 29:
                update_config("GSC Driver Yellow Bang", enable=True, logdir=logdir)
                tracer.csme_yellowbang(mode="gsc")
            if LogType == 30:
                update_config("AUX Driver Yellow Bang", enable=True, logdir=logdir)
                tracer.csme_yellowbang(mode="_aux")
            if LogType == 31:
                tracer.csme_bsod(mode="Tee")
            if LogType == 32:
                tracer.csme_bsod(mode="SPD")
            if LogType == 33:
                tracer.csme_bsod(mode="gsc")
            if LogType == 34:
                tracer.csme_bsod(mode="_aux")
            if LogType == 35:
                tracer.storage()
        except Exception as e:
            logging.exception("Unhandled exception occurred")
            messagebox.showerror(title='Unhandled Exception',message=f"See sit.log for more detail. Error: {e}")
            
        
    logging.info("All traces has returned. Post-processing output directory...")
   
    # change the access of output dir to allow all. 
    tracer.chmod(logdir)
    tracer.cleanup()

    # If any boot trace are run, warn the user about reopening this tool after reboot.
    if any([x["reboot"] for x in queue]):
        messagebox.showwarning(title='Warning',message="You have enabled trace that requires a restart. Restart system and then reproduce your issue(s) if required. After issue is reproduced , launch this tool again and stop the trace.")
        logging.info("All tasks completed. Boot traces are run, so not opening explorer.")
    elif LogType != 29 and LogType != 30:
    # if not, then zip the output dir & open the folder if necessary.
        config = load_config()
        if config['General']['ZipOutput'].lower() == "true":
            zipfolder(logdir)
        logging.info("Task completed. Asking user if open folder...")
        promptdir = messagebox.askyesno(title='Info',
            message="All tasks completed. Please attach the resulting zip file to IPS issue attachment. Do you want to open the folder now?")
        if promptdir:
            logging.info("Opening directory with explorer.exe ...")
            os.system("explorer /select, \"{}\"".format(logdir))
        else:
            logging.info("User denied. Done.")

def format_color(r,g,b):
    return "#{:02x}{:02x}{:02x}".format(r,g,b)

class SITInterface(tk.Tk):
    def __init__(self):
        logging.info('Initializing UI components ...')
        tk.Tk.__init__(self)
        
        self.timestamp = get_date_time()

        self.SPLIT = 13

        # resolve all path
        self.paths = {
            "icon": "300kmh.ico",
            "banner": "banner10.png",
            "splash": "splash_smal",
            "collectall": "CollectAll.png",
            "Execute": "Execute.png",
            "Ingredient": "Ingredient.png",
            "Issue": "Issue.png",
        }
        for k in self.paths:
            self.paths[k] = pjoin(resrc_path, self.paths[k])

        # hide main window when drawing
        self.withdraw()

        # set icon, title
        self.iconbitmap(self.paths["icon"])    
        self.title("Software Issue Tracer v1.3.0")

        # banner
        logging.info('Loading banner...')
        self.banner = ImageLabel(self, self.paths["banner"], background=format_color(0,159,223))
        self.banner.resize((1200,100))
        self.banner.grid(row=0, column=0, columnspan=4, sticky="nswe")

        # config
        self.style_names = self.config_font()

        # init shared values
        self.issue_selection = None
        self.checklist = []

        # create panels
        self.oemframe = self.customer_panel()
        self.qckframe = self.optional_panel()
        self.isuframe = self.issue_panel()
        self.igrframe = self.ingrdient_panel()
        self.cltframe = self.collect_panel()

        self.oemframe.grid(padx=5, pady=5, row=1, column=0, rowspan=1, sticky="nswe")
        self.qckframe.grid(padx=5, pady=5, row=2, column=0, rowspan=1, sticky="nswe")
        self.isuframe.grid(padx=5, pady=5, row=1, column=1, rowspan=2, sticky="nswe")
        self.igrframe.grid(padx=5, pady=5, row=1, column=2, rowspan=2, sticky="nswe")
        self.cltframe.grid(padx=5, pady=5, row=1, column=3, rowspan=2, sticky="nswe")
        
        # bind greyout functions
        self.greyout_bindings()

        # copyright label
        # self.create_copyright_text(rows=4, columns=4)
        CopyrightLabel(self, rows=4, columns=4)

        # allow for resize in these dimensions
        for r in range(1, 3):
            self.grid_rowconfigure(r, weight=1)
        for c in range(4):
            self.grid_columnconfigure(c, weight=1)


        self.show()
        logging.info('Successfully initialized UI components.')

    def show(self):
        self.deiconify()

    def config_font(self):
        logging.info('Configuring font style...')
        # make all text larger
        for name in ["TkDefaultFont", "TkTextFont", "TkFixedFont"]:
            default_font = tkFont.nametofont(name)
            default_font.configure(size=16)

        # Bold and Italic styles
        s = ttk.Style()
        style_names = {}
        s.configure('Bold.TLabelframe.Label', font=('helvetica', 16, 'bold italic'))
        style_names["LabelFrame"] = 'Bold.TLabelframe'

        s.configure('Italic.TLabel', font=('helvetica', 16, 'italic'))
        style_names["Instruction"] = 'Italic.TLabel'

        return style_names

    def greyout_bindings(self):
        logging.info('Binding grayout events to actions...')
        self.disable_frame(self.qckframe)
        self.disable_frame(self.isuframe)
        self.disable_frame(self.igrframe)
        self.disable_frame(self.cltframe)

        # bindings for "Project Name"
        def text_entered():
            text1, text2 = self.get_customer_name(cat=False, check=False)
            if text1 == "" or text2 == "":
                self.disable_frame(self.qckframe)
                self.disable_frame(self.isuframe)
                self.disable_frame(self.igrframe)
                self.disable_frame(self.cltframe)
            else:
                self.enable_frame(self.qckframe)
                self.enable_frame(self.isuframe)

        self.oem_name.trace("w", lambda *args:self.after(1, text_entered))
        self.proj_name.trace("w", lambda *args:self.after(1, text_entered))

        # bindings for "Issue types"
        # is already done in "suggest_trace"

        # bindings for "Ingredient Selection"
        # is already done in "on_item_checked"    

    def customer_panel(self):
        logging.info('Creating customer panel...')
        
        frame = ttk.LabelFrame(self, text="Step 1: Input Project Name", style=self.style_names["LabelFrame"])
        
        self.oem_name = tk.StringVar()
        self.proj_name = tk.StringVar()

        label1 = ttk.Label(frame, text="OEM")
        entry1 = ttk.Entry(frame, textvariable=self.oem_name, width=12)

        label2 = ttk.Label(frame, text="Project")
        entry2 = ttk.Entry(frame, textvariable=self.proj_name, width=12)

        label1.grid(padx=2, pady=2, row=0, column=0, sticky="nswe")
        label2.grid(padx=2, pady=2, row=0, column=1, sticky="nswe")
        entry1.grid(padx=2, pady=2, row=1, column=0, sticky="nswe")
        entry2.grid(padx=2, pady=2, row=1, column=1, sticky="nswe")

        return frame

    def get_customer_name(self, cat=True, check=True):
        oem = self.oem_name.get()
        proj = self.proj_name.get()
        if check:
            if oem == "":
                messagebox.showerror(title='Error',message='Please provide customer first!')
                return
            elif proj == "":
                messagebox.showerror(title='Error',message='Please provide project name!')
                return
        if cat:
            return oem+"-"+proj
        return oem, proj


    def quick_launch(self):
        strOEM = self.get_customer_name()        

        queue = [d for d in uiconfig.INGREDIENTS.values() if d["type"] in ("log", "config")]

        execute(strOEM, queue, time=self.timestamp)

    def reg_clear(self):
        strOEM = self.get_customer_name()        

        execute(strOEM, [], time=self.timestamp, reset=True)

    def optional_panel(self):
        logging.info('Creating optional panel...')
        frame = ttk.LabelFrame(self, text="Optional", style=self.style_names["LabelFrame"])
        
        config_button = ttk.Button(frame, text="Collect All Configs and Dumps", width=27,
            command=self.quick_launch)
        config_button.grid(padx=5, pady=5, row=0, column=0, sticky="nswe")

        regclr_button = ttk.Button(frame, text="Reset registry keys set by SIT", width=27,
            command=self.reg_clear)
        regclr_button.grid(padx=5, pady=5, row=1, column=0, sticky="nswe")

        # windbg_button = ttk.Button(buttonsframe, text="Enable WinDBG")
        # windbg_button.grid(padx=5, pady=5, row=1, column=0, sticky="nswe")

        # adding systeminfo trace
        t = "System Information"
        selection = ttk.Checkbutton(frame, text=t)
        selection.text = t
        selection.state(['!alternate', '!selected', '!disabled'])
        selection.grid(padx=5, pady=5, row=2, column=0, sticky="nswe")
        # show tips
        tip = uiconfig.INGREDIENTS[t]["tip"]
        createToolTip(selection, tip)
        self.checklist.append(selection)        
        
        icon_pos = (3, 1)
        icon = ImageLabel(frame, self.paths["collectall"], background="#f0f0f0")
        icon.resize((60,60))
        icon.grid(row=icon_pos[0], column=icon_pos[1], sticky="se")

        # this is so the icon can correctly stick to the sides
        frame.grid_rowconfigure(icon_pos[0], weight=1)
        frame.grid_columnconfigure(icon_pos[1], weight=1)

        return frame

    def issue_panel(self):
        logging.info('Creating Issue panel...')
        """issue selection"""
        issueframe = ttk.LabelFrame(self, text="Step 2: Select Issue Type", style=self.style_names["LabelFrame"])
        
        issue_value = tk.StringVar()

        for pos,iss in enumerate(sorted(uiconfig.ISSUETYPES.keys())):
            logging.info(f'Adding issue \"{iss}\" at \"{pos}\"')
            b = ttk.Radiobutton(issueframe, text=iss,
             variable=issue_value, value=iss,
             command=self.suggest_trace)

            # add tooltip for button
            tip = uiconfig.ISSUETYPES[iss]["tip"]
            createToolTip(b, tip)

            b.grid(padx=2, pady=2, row=pos % self.SPLIT, column=pos // self.SPLIT, sticky="NSWE")

        columns = int(math.ceil(len(uiconfig.ISSUETYPES)/self.SPLIT))
        for c in range(columns):
            issueframe.columnconfigure(c,weight=1, uniform='issueops')
        
        icon = ImageLabel(issueframe, self.paths["Issue"], background="#f0f0f0")
        icon.resize((60,60))
        icon.grid(row=self.SPLIT, column=2, sticky="se")

        # this is so the icon can correctly stick to the sides
        issueframe.grid_rowconfigure(self.SPLIT, weight=1)
        issueframe.grid_columnconfigure(2, weight=1)

        self.issue_selection = issue_value
        return issueframe

    def create_trace_selection(self,frame):        
        buttonList = []
        
        for t, conf in sorted(uiconfig.INGREDIENTS.items()):
            logging.info(f'Adding trace \"{t}\"')
            trace_selection = ttk.Checkbutton(frame, text=t, command=lambda e=t: self.on_item_checked(e))
            trace_selection.text = t
            trace_selection.state(['!alternate', '!selected', '!disabled' if conf["id"] in uiconfig.AVAILABLE else 'disabled'])
            
            # show tips
            tip = conf["tip"]
            createToolTip(trace_selection, tip) 

            buttonList.append(trace_selection)

            # for the initial option (N/A)
            if conf["id"] < 0:           
                trace_selection.grid(padx=2, pady=2, row=0, column=0, sticky="NSWE")
                         

        # at least one column, 5 rows
        # this ensures that the frame is not collapsed when options are not enough
        for i in range(self.SPLIT):
            frame.grid_rowconfigure(i, minsize=40)
        # frame.grid_columnconfigure(0, minsize=200)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        return buttonList

    def ingrdient_panel(self):
        logging.info('Creating Ingredient panel...')
        """Powertrace Selection"""
        traceframe = ttk.LabelFrame(self, text="Step 3: Select Ingredient(s)", style=self.style_names["LabelFrame"])
        checklist = self.create_trace_selection(traceframe)

        icon = ImageLabel(traceframe, self.paths["Ingredient"], background="#f0f0f0")
        icon.resize((60,60))
        icon.grid(row=self.SPLIT, column=1, rowspan=2, sticky="se")

        # this is so the icon can correctly stick to the sides
        traceframe.grid_rowconfigure(self.SPLIT, weight=1)
        traceframe.grid_columnconfigure(1, weight=1)

        # insert at begining, so that it sysinfo can be at the last.
        self.checklist = checklist + self.checklist
        return traceframe

    def collect_panel(self):
        logging.info('Creating Collect panel...')
        """buttons"""
        buttonsframe = ttk.LabelFrame(self, text="Step 4: Collect", style=self.style_names["LabelFrame"])
        
        ok_button = ttk.Button(buttonsframe, text="Start", command=self.ready)
        ok_button.grid(padx=5, pady=5, row=0, column=0, sticky="s")

        cancel_button = ttk.Button(buttonsframe, text="Cancel", command=self.abort)
        cancel_button.grid(padx=5, pady=5, row=1, column=0, sticky="s")

        # default_button = ttk.Button(buttonsframe, text="Default", command=self.abort)
        # default_button.grid(padx=5, pady=5, row=2, column=0, sticky="s")

        exe_icon = ImageLabel(buttonsframe, self.paths["Execute"], background="#f0f0f0")
        exe_icon.resize((60,60))
        exe_icon.grid(row=2, column=0, sticky="se")

        # this is so the icon can correctly stick to the sides
        buttonsframe.grid_rowconfigure(2, weight=1)
        buttonsframe.grid_columnconfigure(0, weight=1)

        return buttonsframe

    def ready(self):
        logging.info('User pressed Start, checking input integrity...')

        strOEM = self.get_customer_name()
        issue_str = self.issue_selection
        trace_list = self.checklist

        ISSUETYPE = issue_str.get()

        if ISSUETYPE == "":
            # not likely to happen because Start is greyed out if no issue selected.
            logging.info('Issue type was not selected. Aborted.')
            messagebox.showerror(title='Error',message='Please select issue type first!')
            return
            
        queue = []
        for box in trace_list:
            if box.instate(['selected']):
                LogType = uiconfig.INGREDIENTS[box.text]
                queue.append(LogType)

        logging.info(f"Customer name: {strOEM}")
        logging.info(f"Pending trace(s): {queue}")
        
        execute(strOEM, queue, time=self.timestamp)

    def abort(self):
        logging.info('User pressed Cancel, clearing all input & grey out...')
        ## clears oem
        self.oem_name.set("")
        self.proj_name.set("")
        ## clears issue
        self.issue_selection.set(None)
        ## clears ingredient
        self.suggest_trace()
        ## disable frames
        self.disable_frame(self.qckframe)
        self.disable_frame(self.isuframe)
        self.disable_frame(self.igrframe)
        self.disable_frame(self.cltframe)

    def suggest_trace(self):        
        # enable the icon
        self.enable_frame(self.igrframe)

        issue = self.issue_selection.get()

        if issue not in uiconfig.ISSUETYPES: # not likely ti happen
            logging.error("Issue \"{}\" not recognized.".format(issue))
            return

        shown_options = uiconfig.ISSUETYPES[issue]["ingredients"]
        defaults = uiconfig.ISSUETYPES[issue]["default"]
        
        pos = 0
        for box in self.checklist:
            # avoid running grid_forget for the "system performance" option.
            if box.master != self.igrframe:
                continue

            i = uiconfig.INGREDIENTS[box.text]["id"]

            # reset state
            box.state(['!selected', ('!disabled' if i in uiconfig.AVAILABLE else 'disabled')])

            if i in shown_options:
                # if row starts at 1 it's because of the label "select traces"
                box.grid(padx=2, pady=2, row=pos % self.SPLIT, column=pos // self.SPLIT, sticky="NSWE")
                pos += 1

                if i in defaults:
                    box.state(['selected'])
            else:
                box.grid_forget()
        # update according to items checked
        self.on_item_checked()



    def on_item_checked(self, caller=None):
        self.exclude_trace(caller)
        n_selected = 0
        for box in self.checklist:
            if box.instate(['selected']):
                logging.debug(box.text+" selected.")
                n_selected += 1
        if n_selected == 0:
            self.disable_frame(self.cltframe)
        else:
            self.enable_frame(self.cltframe)                

    def exclude_trace(self, caller=None):
        if caller is None:
            return
        group = []
        i = uiconfig.INGREDIENTS[caller]["id"]
        issue = self.issue_selection.get()
        group = uiconfig.ISSUETYPES[issue]["exclusive"]
        if isinstance(group[0], list):
            for ll in group:
                if i in ll:
                    for box in self.checklist:
                        j = uiconfig.INGREDIENTS[box.text]["id"]
                        if j!=i and j in ll:
                            box.state(['!selected'])
        else:    
            for box in self.checklist:
                j = uiconfig.INGREDIENTS[box.text]["id"]
                if j!=i and j in group:
                    box.state(['!selected'])
       
    def disable_frame(self, frame):
        for child in frame.winfo_children():
            if isinstance(child, ttk.Checkbutton):
                child.state(['!selected', 'disabled'])
            else:
                child.configure(state='disable')

    def enable_frame(self, frame):
        for child in frame.winfo_children():
            if isinstance(child, ttk.Checkbutton):
                child.state(['!selected', '!disabled'])
            else:
                child.configure(state='enable')


def load_config(name='settings.ini'):
    logging.info(f"Loading configuration from {name}...")
    config = configparser.ConfigParser()        
    if os.path.isfile(name):
        config.read(name)
    else:
        logging.info(f"Creating new configuration file...")
        config['BootTraces'] = {}
        config['General'] = {'ZipOutput':True}

    with open(name, 'w') as configfile:
        config.write(configfile)
    return config

def update_config(boottrace, enable, logdir="", name='settings.ini'):
    logging.info(f"Updating config file...")
    config = configparser.ConfigParser()
    if not os.path.isfile(name):
        logging.error("Failed to create config file or config is deleted manually. Please retry.")
        return
    
    pool = [s.lower() for s in uiconfig.INGREDIENTS]
    if boottrace.lower() not in pool:
        logging.error(f"Failed to update config because \"{boottrace}\" is not a supported trace/log/config.")
        raise AssertionError(f"Failed to update config because \"{boottrace}\" is not a supported trace/log/config.")

    config.read(name)
    if enable:
        config['BootTraces'][boottrace] = "Active"
        config['BootTraces']["location"] = logdir
    else:
        try:
            del config['BootTraces'][boottrace]
        except:
            pass
    with open(name, 'w') as configfile:
        config.write(configfile)

def handle_boot_traces(boottraces):
    trace_names = []
    for name, state in boottraces.items():
        if state == "Active":
            trace_names.append(name)

    if len(trace_names) == 0:
        logging.error("No boot trace found active. Aborted.")
        return
    
    zipping = False
    for trace_name in trace_names:
        logging.info(f"Found boot trace {trace_name}, asking user...")
        stopboot = messagebox.askyesno(title="Stop",
            message=f"\"{trace_name}\" is active and running. Do you want to stop it now and collect output(s)?")
        
        if not stopboot:
            logging.info("User denied. Aborted.")
            continue
        
        zipping = True
        # find the id of the ingredient trace
        LogType = -99
        for t,l in uiconfig.INGREDIENTS.items():
            if t.lower() == trace_name:
                LogType = l["id"]
                break

        if LogType == -99:
            logging.error(f"\"{trace_name}\" is not supported in current tool. Aborted.")
            return

        # find the previous working directory to continue in.
        try:
            logdir = boottraces.pop("location") # remove "location" because error
        except KeyError:
            logging.warning("Previous logging directory not found. Creating a new directory.")
            logdir = pjoin(os.getcwd(), "boottrace-"+get_date_time())

        logging.info(f"Ouput directory set to: {logdir}")
        tracer = Traces(logdir=logdir, resrc_path=resrc_path, codec=_codec)

        try:
            if LogType == 14:
                tracer.realtimebsod(stop=True)
            elif LogType == 15:
                tracer.tbt_boot(stop=True)
            elif LogType == 17:
                tracer.isst(stop=True)
            elif LogType == 18:
                tracer.i2c(acpi=False, stop=True)
            elif LogType == 20:
                tracer.i2c(acpi=True, stop=True)
            elif LogType == 21:
                tracer.graphic_boot(stop=True)
            elif LogType == 22:
                tracer.wiman(stop=True)
            elif LogType == 26:
                tracer.dal(stop=True)
            elif LogType == 27:
                tracer.csme_yellowbang(stop=True, mode="Tee")
            elif LogType == 28:
                tracer.csme_yellowbang(stop=True, mode="SPD")
            elif LogType == 29:
                tracer.csme_yellowbang(stop=True, mode="gsc")
            elif LogType == 30:
                tracer.csme_yellowbang(stop=True, mode="_aux")
           
            update_config(trace_name, enable=False)
        except Exception as e:
            logging.exception("Unhandled exception occurred")
            messagebox.showerror(title='Unhandled Exception',message=f"See log file for more detail. Error: {e}")
                

    if zipping:
        logging.info("Post-processing output directory...")

        tracer.chmod(logdir)
        tracer.cleanup()

        logging.info("Post-processing done.")

        config = load_config()
        if config['General']['ZipOutput'].lower() == "true":
            zipfolder(logdir)
        
        # pop up message for opening folder.
        logging.info("Task completed. Asking user if open folder...")
        promptdir = messagebox.askyesno(title='Info',
            message="All tasks completed. Please attach the resulting zip file to IPS issue attachment. Do you want to open the folder now?")
        if promptdir:
            logging.info("Opening directory with explorer.exe ...")
            os.system("explorer /select, \"{}\"".format(logdir))
        else:
            logging.info("User denied. Done.")


def main():
    global _codec
    # 0. init logging
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s', 
        # datefmt='%d-%b-%y %H:%M:%S',
        level=logging.INFO, # INFO
        handlers=[
            logging.FileHandler("sit.log", mode="a", encoding=_codec),
            logging.StreamHandler(sys.stderr)
        ]
        )

    logging.info('Logger initialized succussfully.')

    # 1. try to kill the splash screen by pid passed in by launch.bat
    if len(sys.argv) > 1:
        try:
            logging.info(f'PID passed as {sys.argv[1]} for splashscreen.')
            splash_pid = int(sys.argv[1])
            if len(sys.argv) > 2:
                _codec = str(sys.argv[2])
            p = psutil.Process(splash_pid)
            if p.name() == "mshta.exe":
                logging.info('Terminating mshta.exe ...')
                subprocess.call("@taskkill /PID {} /F >nul 2>&1".format(splash_pid), shell=True)
                logging.info('Successfully terminated mshta.exe (splash screen).')
        except:
            raise

    # 1. checkini
    logging.info('Loading configuration from settings.ini ...')
    config = load_config()
    #### debug function: if debug mode, set resource dir to dist/resource
    global resrc_path
    if 'debug' in config['General']:
        logging.warning('Debug mode is enabled!!!')
        resrc_path = pjoin(os.path.abspath(os.path.dirname(__file__)), "dist", "resource")

    # 2. init UI
    win = SITInterface()

    # 3. handle boot trace
    if len(config['BootTraces']) > 0:
        handle_boot_traces(config['BootTraces'])
        logging.info('Successfully handled boot traces')
    else:
        logging.info('Successfully loaded config.')

    
        
    # 4. detect cpuinfo
    logging.info('Detecting cpu info ...')
    cpuinfo = platform.processor()
    logging.info(f'CPU info: {cpuinfo}')
    if "intel" not in cpuinfo.lower():
        logging.error('CPU info does not contain intel. Aborting...')
        messagebox.showerror(title="Error", 
            message="The system is detected to be \""+cpuinfo+"\". This tool only supports Intel® platform.")
        return
    logging.info('Successfully found Intel cpu.')

    # 5. enter UI main loop
    win.mainloop()
   

if __name__ == "__main__":    
    main()