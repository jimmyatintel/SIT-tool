import sys
import os
from os.path import join as pjoin
import subprocess
import shutil
import json
import getpass
import csv
import logging
from collections import defaultdict as ddict
import itertools
import glob # for wildcard
import signal # for SIGTERM
import winreg # for registry
import time # for sleep
import re

# for prompts
from tkinter import ttk, messagebox, simpledialog

class Traces(object):
    def __init__(self, logdir, resrc_path, codec):
        r"""
        In general, a trace consists of the following steps:
        1. Run the specific batch script file
        2. Copy/Move the resulting log file to logdir

        Some traces that involves reboot will have an argument "stop",
        1. Run start trace batch
        2. User reproduce issue (which involves rebooting)
        3. User re-open SIT Tool
        4. SIT tool automatically runs stop trace batch for that trace.
        """


        logging.info(f"Initializing tracer instance ...")
        self.resrc_path = os.path.abspath(resrc_path)
        if not os.path.isdir(self.resrc_path):
            logging.error(f"Cannot find resource directory at: {self.resrc_path}")
            raise FileNotFoundError("path "+self.resrc_path+" is not found.")

        self.scripts = ddict(dict)
        self._tmp_dir = self.resrc_path #pjoin(tempfile.gettempdir(), "SITTempDir")

        if logdir is not None:
            self.logdir = os.path.abspath(logdir)
            self.mkdir(self.logdir)
        else :
            self.logdir = None

        self.powershell = False
        self.codec = codec

        logging.info(f"Log dir at: {self.logdir}")
        logging.info(f"Resource dir at: {self.resrc_path}")
        logging.info(f"Temp dir at: {self._tmp_dir}")
        logging.info(f"Using powershell: {self.powershell}")
        logging.info(f"Log dir at: {self.logdir}")
        logging.info(f"Using codec: {self.codec}")

        logging.info(f"Initialized tracer instance successfully.")

    def cleanup(self):
        pass
        # logging.info(f"Cleaning garbage: {self.garbage}")
        # for e in self.garbage:
        #     # both returns false when not exist
        #     if os.path.isfile(e):
        #         os.remove(e)
        #     elif os.path.isdir(e):
        #         shutil.rmtree(e)

    def move(self, src, tgt):
        try:
            if os.path.isfile(src) or os.path.isdir(src):
                logging.info(f"Moving: \"{src}\" -> \"{tgt}\"")
                shutil.move(src, tgt)
            else:                
                logging.warning(f"\"{src}\" ignore for not existing.")
        except Exception as e:
            logging.exception("Exception occurred")

    def copy(self, src, tgt):
        try:
            if os.path.isdir(src):
                logging.info(f"Copying: \"{src}\" -> \"{tgt}\"")
                shutil.copytree(src, tgt)
            elif os.path.isfile(src):
                logging.info(f"Copying: \"{src}\" -> \"{tgt}\"")
                shutil.copy2(src, tgt)
            else:                
                logging.warning(f"\"{src}\" ignore for not existing.")
        except Exception as e:
            logging.exception("Exception occurred")

    def mkdir(self, path):
        logging.info(f"Creating directory at: {path}")
        try:
            os.makedirs(path)
        except FileExistsError:
            logging.warning(f"Target directory \"{path}\" already exists. Ignoring command.")

    def chmod(self, folder):
        """
        Some copied folders will still require administrator right to access, 
        so we have to change the permission.
        """
        commands = [
        "@echo off",
        "set folder={0}".format(folder),
        "cd /d %folder%",
        "icacls * /t /grant:r \"everyone:(OI)(CI)F\""
        ]

        script = " & ".join(commands)
        
        self.runbg(script, folder)


    
    def runat(self, name, at):
        """
        Warning: sometimes when running a single command, this command will fail.
        Sol: you can append useless command in name, like so: cmd="hello.bat & echo done"
        """
        logging.info(f"Running command(s) \"{name}\" at \"{at}\"")
        if self.powershell:
            fullcmd = """powershell.exe -Command "Start-Process -FilePath cmd.exe -ArgumentList '/c', '{}' -WorkingDirectory '{}' -Verb runAs -Wait"
            """.format(name, at)
        else:
            fullcmd = """start "Software Issue Tracer v1.3.0" /Wait /D "{}" cmd.exe /c "{}" /Wait
            """.format(at, name)
        subprocess.call(fullcmd.strip(), shell=True)
        logging.info(f"Command completed.")

    def runbg(self, name, at):
        logging.info(f"Running background command(s) \"{name}\" at \"{at}\"")       
        p = subprocess.Popen(name, cwd=at, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        rc = p.returncode
        status = {"stdout":out.decode(self.codec), "stderr":err.decode(self.codec), "return":rc}
        logging.info(f"Command returned with status: {status}")
        if rc != 0:
            logging.warning("The previous command returned with nonzero return code, see previous message for error details.")

        return status

    def gui_ask_type(self, title, msg, dtype):
        """So far this is only used in highloadingactivities trace
        where the tool asks user for desired timeout in seconds.
        """
        ret = None
        while ret == None:
            ret = simpledialog.askstring(title, msg)
            if ret != None:
                try:
                    ret = dtype(ret)
                except ValueError:
                    logging.error("Cannot convert \"{}\" to type \"{}\"".format(ret, dtype))
                    ret = None
            else:
                # user cancelled
                break
        return ret
    def regclr(self):
        logging.info("Reset registries modified by SIT tool...")

        regs = [
            # ISST
            r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\WMI\Autologger\ISST",
            r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\WMI\Autologger\AudioSST",
            # CSME
            r"HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\Tee",
            r"HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\Spd",
            r"HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\Gsc",
            r"HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\Auxi",
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Intel\Services\DAL",
            r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\jhi_service"
        ]       

        regsinfo = "\n\n".join(regs)

        checkdel = messagebox.askyesno(title='Warning',
            message=f"This will reset the following registry keys\n\n{regsinfo}\n\nDo you want to continue?")
        if checkdel:
            for reg in regs:
                command = f"reg delete {reg} /f"
                self.runbg(command, ".")
            messagebox.showinfo(title="Info",
                message="Registry keys reset successfully.")
        else:
            logging.info("User denied. Done.")


    def sysinfo(self, outname='systeminfo'):
        logging.info("Running System Info Collection...")

        messagebox.showwarning(title='Collecting System Info',
            message="This may take a while (5-10 minutes), please wait while the tool "
            "collects system information.")
        
        outdir = pjoin(self.logdir, outname)
        self.mkdir(outdir)

        # run msinfo and copy to outdir
        self.runbg(r"msinfo32 /report system-msinfo32.txt", self._tmp_dir)
        f = "system-msinfo32.txt"
        self.move(pjoin(self._tmp_dir, f), pjoin(outdir, f))

        # copy other infos
        files = [
        (r"c:\windows\System32\winevt","Logs"),
        (r"c:\windows\panther","setupact.log"),
        (r"c:\windows\INF","setupapi.setup.log"),
        ]

        for srcdir, f in files:
            src = pjoin(srcdir, f)
            tgt = pjoin(outdir, f)
            self.copy(src, tgt)

    def marker(self):
        logging.info("Setting marker event...")
        gfxtemp = pjoin(self._tmp_dir, "GfxEvents")

        messagebox.showwarning(title='Setting marker event...',
            message=f"Please use Alt+Ctrl+1,2,3..to make the issue event.\n\nExample:\n\"Alt+Crtl+1= issue appear\"\n\"Alt+Crtl+2= issue disappear\".")
        p = subprocess.Popen("EventGenerator.exe", cwd=gfxtemp, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


    def usb(self, outname='usbtrace.etl'):
        logging.info("Running USB trace...")
        name = pjoin(self._tmp_dir, '_usb_trace.cmd')

        self.runat(name, '.')

        src = pjoin(self._tmp_dir, 'usbtrace.etl')
        tgt = pjoin(self.logdir, outname)
        self.move(src, tgt)
        
    def highloadingactivities(self, outname='system_performance.etl'):
        logging.info("Running High Loading Activities trace...")
        name = pjoin(self._tmp_dir, "_ModernStandbyETW.cmd")

        sec = self.gui_ask_type("Timeout", "Please enter value for timeout (sec):", int)
        if sec == None:
            logging.info("User cancelled operation.")
            return

        cmd = f"{name} {sec}"
        self.runat(cmd, '.')

        src = pjoin(self._tmp_dir, "idle.etl")
        tgt = pjoin(self.logdir, outname)
        self.move(src, tgt)

    def idle(self, outname='idle.etl'):
        logging.info("Running Idle trace...")
        name = pjoin(self._tmp_dir, "_IdleLog.cmd")

        self.runat(name, '.')

        src = pjoin(self._tmp_dir, "idle.etl")
        tgt = pjoin(self.logdir, outname)
        self.move(src, tgt)
        

    def livedumpfile(self, outname='memory.dmp'):
        logging.info("Running Live Dump File...")
        messagebox.showinfo(title='Instructions',
            message="Please follow the instructions before preceeding:\n"
            "1. Insert USB storage device larger than system memory.\n"
            "2. Create folder \"NTFS_LIVEKD_MEMORY_DMP\" in such USB device.\n"
            "3. Ensure internet connection for symbol download.")

        name = pjoin(self._tmp_dir, "_LiveDumpFile.cmd")
        
        self.runat(name, '.')

    def tbt_boot(self, stop=False, outname='TBT_SINGLE_BOOT_LOG'):
        logging.info(f"Running TBT trace(boot)...")
        tbttemp = pjoin(self._tmp_dir, "ThunderboltTrace") 

        """Now execute required files"""
        startname = "StartSingleBootTrace.bat"
        name = "StopBootTrace.bat" if stop else startname
        
        self.runat(name, tbttemp)

        if stop:
            for entry in os.listdir(tbttemp):
                if 'TBT_SINGLE_BOOT_LOG' in entry:
                    src = pjoin(tbttemp, entry)
                    tgt = pjoin(self.logdir, outname)
                    self.move(src, tgt)
                    
    def tbt(self, outname='TBT_LOG'):
        logging.info("Running TBT trace...")
        
        tbttemp = pjoin(self._tmp_dir, "ThunderboltTrace")

        """Now execute required files"""
        commands = [
        "@mkdir \"TBT_LOG_\"",
        "StartTrace.bat TBT_LOG_",
        "@echo #########################################################################",
        "@echo # Log is currently being collected and will stop once you press any key",
        "@echo #########################################################################",
        "pause",
        "StopTrace.bat",
        "@echo Log is complete."
        ]

        script = " & ".join(commands)
        
        self.runat(script, tbttemp)

        for entry in os.listdir(tbttemp):
            if "TBT_LOG_" in entry:
                src = pjoin(tbttemp, entry)
                tgt = pjoin(self.logdir, outname)
                self.move(src, tgt)

    def display(self, outname='Display.etl'):
        logging.info("Running Display trace...")
        """"""
        gfxtemp = pjoin(self._tmp_dir, "GfxEvents")

        """Now execute required files"""
        run = ["Install.bat", "Trace.bat"]
        for name in run:
            self.runbg(name, gfxtemp)

        logging.info(f"Starting display trace.")

        messagebox.showwarning(title="trace running...", 
            message="Trace is running. Press \"OK\" to stop the trace.")

        logging.info('Stoping display trace.')

        self.runbg("Trace.bat", gfxtemp)

        logging.info('Success. Copying files...')
        src = pjoin(gfxtemp, "GfxTrace.etl")
        tgt = pjoin(self.logdir, outname)        
        self.move(src, tgt)

    def graphic_boot(self, stop=False, outname='MergGfxBootTrace.etl'):
        logging.info("Running graphic boot trace...")

        """"""
        gfxtemp = pjoin(self._tmp_dir, "GfxEvents")

        """Now execute required files"""
        if not stop:
            run = ["Install.bat", "BootTrace.bat --perf"]
        else: 
            run = ["BootTrace.bat"]
        for name in run:
            self.runbg(name, gfxtemp)

        if stop :
            logging.info('Success. Copying files...')
            src = pjoin(gfxtemp, "MergGfxBootTrace.etl")
            tgt = pjoin(self.logdir, outname)        
            self.move(src, tgt)

    def video_performance(self, outname='video_performance.etl'):
        logging.info("Running video performance trace...")
        gpuviewdir = r"C:\Program Files (x86)\Windows Kits\10\Windows Performance Toolkit\gpuview"
        if not os.path.isdir(gpuviewdir):
            logging.error(f"Cannot find directory \"{gpuviewdir}\".")
            msg = "The tool failed to locate gpuview at \"" + gpuviewdir + "\". Please install Windows ADK properly before running the tool."
            raise FileNotFoundError(msg)

        """Now execute required files"""

        commands = [
        "log.cmd",
        "@echo #########################################################################",
        "@echo # Log is currently being collected and will stop once you press any key",
        "@echo #########################################################################",
        "pause",
        "log.cmd",
        "@echo Log is complete.",
        ]

        script = " & ".join(commands)

        self.runat(script, gpuviewdir)

        src = pjoin(gpuviewdir, "Merged.etl")
        tgt = pjoin(self.logdir, outname)
        self.move(src, tgt)

    def realtimebsod(self, stop=False, outname='GfxRealTimeTrace.etl'):
        logging.info(f"Running realtime bsod trace (stop={stop})...")
        exedir = pjoin(self._tmp_dir, "GfxEvents")

        if not stop:
            status = self.runbg("Trace.bat --RealTime", exedir)
            msg = status['stderr'] # status['stdout'] + "\n" + 
            if msg:
                messagebox.showwarning(title="info", message=msg)
        else:
            status = self.runbg("Trace.bat --RealTime", exedir)
            msg = status['stderr'] # status['stdout'] + "\n" + 
            if msg:
                messagebox.showwarning(title="info", message=msg)
            logging.info("Copying log file...")
            src = pjoin(exedir, "GfxRealTimeTrace.etl")
            tgt = pjoin(self.logdir, outname)            
            self.move(src, tgt)
    
    def rst(self, outname='rst.log'):
        logging.info("Running RST log collection...")
        
        rsttemp = pjoin(self._tmp_dir, "RST")
        

        commands = [
        "@echo off",
        # "cd %~dp0", sincer there is no file
        r".\Rstcli64.exe --disableVersionCheck --version >> .\rst.log",
        r".\Rstcli64.exe --disableVersionCheck -I >> .\rst.log",
        r".\Rstcli64.exe --disableVersionCheck --OptaneMemory --info >> .\rst.log",
        r".\Rstcli64.exe --disableVersionCheck --accelerate --stats >> .\rst.log",
        "echo Command completed successfully.",
        ]

        script = " & ".join(commands)

        """Now execute required files"""
        self.runat(script, rsttemp)


        src = pjoin(rsttemp, "rst.log")
        tgt = pjoin(self.logdir, outname)
        self.move(src, tgt)
        
    def optane(self, ):
        logging.info("Running Optane log collection...")
        user = getpass.getuser()
        srcs =[
        pjoin("C:\\", "Windows", "system32", "WINEVT", "LOGS"),
        pjoin("C:\\", "Users", user, "AppData", "Local", "Packages", "AppUp.IntelOptaneMemoryandStorageManagem"),
        pjoin("C:\\", "Users", user, "Intel", "logs"),
        ]
        tgts = [
        pjoin(self.logdir, "winevt", "logs"),
        pjoin(self.logdir, "AppUp.IntelOptaneMemoryandStorageManagem"),
        pjoin(self.logdir, "intel", "logs"),
        ]
        for src,tgt in zip(srcs, tgts):
            self.copy(src, tgt)

    def acpi(self, outname="acpidump\\"):
        logging.info("Running ACPI code dump...")
        
        exedir = pjoin(self._tmp_dir, "iasl-win")

        """Now execute required files"""
        commands = [
        "acpidump.exe -b",
        "iasl.exe -d *.dat",
        "@echo collection is complete.",
        ]

        script = " & ".join(commands)
        
        self.runat(script, exedir)
        tgt = pjoin(self.logdir, outname)
        self.mkdir(tgt)

        """get all .dat and .dsl files"""
        files = itertools.chain(
            glob.glob(pjoin(exedir, "*.dat")),
            glob.glob(pjoin(exedir, "*.dsl"))
            )

        for src in files:
            self.move(src, tgt)
            
    def re_search(self, pattern, text, params, catch=True):
        try:
            logging.info(f"Search for pattern: {pattern}")
            result = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if result is None:
                logging.error(f"Pattern \"{pattern}\" not found in text.")
            elif isinstance(params, str):
                return result.group(params)
            else:
                return {k:result.group(k) for k in params}            
        except Exception as e:
            if catch:
                logging.exception("Unhandled regex exception occurred.", pattern)
        return None

    def _check_testsigning(self,):
        """ this is for acpi2 (Runtime ACPI) """

        commands = ["bcdedit"]
        script = " & ".join(commands)
        
        result = self.runbg(script, ".")
        status = self.re_search(r"testsigning\s+(?P<status>[a-zA-Z]+)", result["stdout"], "status")
        
        if status == "Yes":
            logging.info("testsiging is ON.")
            return True
        elif status == "No":
            # No
            script = "bcdedit /set testsigning on"
            result = self.runbg(script, ".")
            if "error" in result:
                if "Secure Boot" in result:
                    # secure boot
                    pass
                else:
                    logging.error("Failed to turn on testsigning. Details:\n"+result)
                    return False
            else:
                # success. prompt restart
                messagebox.showwarning(title="Setup Success", 
                    message="Please restart now and open SIT tool again after restart.")
                return True

        # handle secure boot error.
        logging.error("A required value \"testsigning\" is protected by Secure Boot. Please disable Secure Boot and try again.")
        messagebox.showerror(title="Error", 
            message="Please disable Secure Boot and try again.")
        return False
                


    def acpi2(self, outname="runtime_acpi.log"):
        """ Runtime ACPI Code
        runtime_acpi.bat <out> <m>:
            logs information every m seconds to the file <out>.

        We also need control for user to interrupt the execution loop,
        hence we create a subprocess to run runtime_acpi.bat, and then 
        on the main process we await user input by messagebox.showwarning
        """
        if not self._check_testsigning():
            return
        # cmd = "!amli dl"
        exedir = pjoin(self._tmp_dir, "livekd")
        
        #### check for symbol availability
        sym_path = r"c:\\symbols\\ntkrnlmp.pdb\\"
        if os.path.isdir(sym_path):
            logging.info("Symbols are available, but may not be loaded.")
        else:
            messagebox.showwarning(title="Symbol Not Found", 
                message="Please ensure internet connection for symbol download.")
            logging.warning("Symbols are not found. Attempt to download by running livekd64...")
            self.runat("livekd64 -b -c q", exedir)

        #### remove existing log
        src = pjoin(exedir, outname)
        if os.path.isfile(src):
            tgt = src+".back"
            logging.info(f"Found existing log file. Moved to {tgt}")
            # shutil.move(src, tgt)
            self.move(src, tgt)
            # os.remove(src)

        script = [
        pjoin(exedir, "runtime_acpi.bat"),
        outname,
        "10" # polling seconds
        ]
        sub = subprocess.Popen(script)
        logging.info(f"Subprocess created. PID={sub.pid}")

        messagebox.showwarning(title="trace running...", 
            message="Trace is running. Press \"OK\" to stop the trace.")

        logging.info('Terminating subprocess ...')
        # subprocess.call("@taskkill /PID {} /F >nul 2>&1".format(sub.pid), shell=True)
        sub.terminate()        
        sub.communicate()
        logging.info('Successfully terminated subprocess.')

        src = pjoin(exedir, outname)
        tgt = pjoin(self.logdir, outname)
        self.move(src, tgt)
        for i in range(5):
            try:
                self.move(src, tgt)
                break
            except :
                logging.warning("Failed to move directory, the subprocess might still be alive, retrying in 1 sec...")
                time.sleep(5)
        
   
    def isst(self, stop=False, outname="isst"):
        logging.info(f"Running iSST trace (stop={stop})...")
        
        exedir = pjoin(self._tmp_dir, "ISST_Autologger")

        if not stop:
            # self.runat("ISST_Autologger_enabled.reg", exedir)
            self.runbg("ISST_Autologger_enabled.reg", exedir)
        else:
            logging.info("Disabling auto logging...")
            commands = [
            "wpp_stop.bat",
            "Disable_ISST__auto_logger.reg"
            ]
            self.runbg(" & ".join(commands), exedir)
            
            logging.info("Copying log files...")
            tgtdir = pjoin(self.logdir, outname)
            self.mkdir(tgtdir)

            self.move(r"C:\ISST.etl", tgtdir)


            files = itertools.chain(
                glob.glob(r"C:\Windows\System32\cAVS\ExtLibs\*.bin"),
                glob.glob(r"C:\Windows\System32\cAVS\*.bin"),
                glob.glob(r"C:\Windows\ServiceState\IntcOED\Data\*.*"),
                glob.glob(r"C:\windows\ServiceState\IntelAudioService\Data\*.*"),
                glob.glob(r"C:\windows\system32\cavs\IAS\*.*"),
                )

            for src in files:
                self.copy(src, tgtdir)

            logging.info("Collecting registry values...")

            for key in ["IntcAudioBus", "IntcOED", "IntelAudioService"]:
                tgt = pjoin(tgtdir, f"{key}.reg")
                command = f"reg export HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\{key} {tgt} & "
                self.runbg(command, ".")

    def i2c(self, acpi=False, stop=False, outname="i2ctrace.etl"):
        logging.info(f"Running I2C trace (stop={stop}, acpi={acpi})...")

        exedir = pjoin(self._tmp_dir, "I2C_log")

        if not stop:
            if acpi:
                self.runbg("i2clog_autostart_ACPI_HIDI2C_WPP.bat", exedir)
            else:
                self.runbg("i2clog_autostart_HIDI2C_WPP.bat", exedir)
        else:
            logging.info("Disabling auto logging...")
            self.runbg("i2clog_autostop.bat", exedir)
            
            logging.info("Copying log file...")
            src = pjoin(exedir, "i2ctrace.etl")
            tgt = pjoin(self.logdir, outname)            
            self.move(src, tgt)

    def wiman(self, stop=False, outname="wiman log"):
        logging.info("Running Wiman driver trace...")

        """"""
        wimantemp = pjoin(self._tmp_dir, "CSME", "WiMan_log")

        """Now execute required files"""
        
        if not stop:
            ctl = pjoin(wimantemp, "WiMan.ctl")
            self.copy(ctl, "C:\\")

            self.runbg("powershell.exe Set-ExecutionPolicy RemoteSigned -Force", ".")
            self.runbg(r"powershell.exe .\wizard.ps1 -trace", wimantemp)
        else:
            src = pjoin(wimantemp, "trace")
            tgt = pjoin(self.logdir, outname)

            self.runbg(r"powershell.exe .\wizard.ps1 -trace_stop", wimantemp)
            self.move(src, tgt)

    
    def installer(self, outname="installer log"):
        logging.info("Collecting installer driver logs...")        
        user = getpass.getuser()

        files = itertools.chain(glob.glob(r"C:\Windows\INF\setupapi.*.log"))
        
        srcs = [
            pjoin("C:\\", "Users", user, "Intel", "Logs", "IntelME.log"),
            pjoin("C:\\", "Users", user, "Intel", "Logs", "IntelME_MSI.log"),
            pjoin("C:\\", "Users", user, "Intel", "Logs", "DifXFrontend.log"),
        ]
        
        tgtdir = pjoin(self.logdir, outname)
        self.mkdir(tgtdir)

        for src in files:
            self.copy(src, tgtdir)
        for src in srcs:
            self.copy(src, tgtdir)
       
    def lms(self, outname="Gms.log"):
        logging.info("Collecting LMS driver log...")

        src = pjoin("C:\\", "Windows", "SysWOW64", "Gms.log")
        tgt = pjoin(self.logdir, outname)

        self.copy(src, tgt)
    
    def icls(self, outname="iCLS"):
        logging.info("Collecting iCLS driver logs...")        

        sysroot = os.getenv('SystemRoot')
        appdata = os.getenv('APPDATA')
        progdata = os.getenv('ProgramData')
        srcs = [
            pjoin(sysroot, "System32", "config", "systemprofile", "AppData", "Local", "Intel", "iCLS Client", "log"),
            pjoin(sysroot, "System32", "LogFiles", "WMI", "Intel", "iCLSClient"),
            pjoin(appdata, "..", "Local", "Intel", "iCLS Client", "log"),
            pjoin(progdata, "Intel", "iCLS Client", "log"),
        ]

        tgtdir = pjoin(self.logdir, outname)

        for src in srcs:
            self.copy(src, tgtdir)


    def dal(self, stop=False, outname="jhi_log.txt"):
        logging.info("Running DAL driver boot trace...")

        """"""
        daltemp = pjoin(self._tmp_dir, "CSME", "DAL")

        """Now execute required files"""
        if not stop:
            run = ["Set universal JHI log level to debug.reg", "Set legacy JHI log level to debug.reg"]
            for reg in run:
                self.runbg(reg, daltemp)
        else: 
            logging.info('Success. Copying files...')
            src = pjoin("C:\\", "jhi_log.txt")
            tgt = pjoin(self.logdir, outname)        
            self.move(src, tgt)
    
    def csme_yellowbang(self, stop=False, mode="Tee", outname="MEI"):
        logging.info(f"Running MEI driver Yellow Bang {mode} boot trace...")

        if not stop:
            """ Delete registry if exist to avoid setting mix up """
            if mode == "Tee":
                self.runbg(r"reg delete HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\Tee /f", ".")
            elif mode == "SPD":
                self.runbg(r"reg delete HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\Spd /f", ".")
            elif mode == "gsc":
                self.runbg(r"reg delete HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\Gsc /f", ".")
            elif mode == "_aux":
                self.runbg(r"reg delete HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\Aux /f", ".")

            """"""
            meitemp = pjoin(self._tmp_dir, "CSME", "MEI", f'{mode}')

            mode = "aux" if mode == "_aux" else mode 

            """Now execute required files"""
            reg = f"trace_enable_{mode}.reg"

            self.runbg(reg, meitemp)
        else:
            if 'PROGRAMFILES(X86)' in os.environ:
                if mode == "Tee":
                    self.runbg("tracelog.exe -stop tee", os.getenv('PROGRAMFILES(X86)'))
                elif mode == "SPD":
                    self.runbg("tracelog.exe -stop spd", os.getenv('PROGRAMFILES(X86)'))
                elif mode == "gsc":
                    self.runbg("tracelog.exe -stop gsc", os.getenv('PROGRAMFILES(X86)'))
                elif mode == "_aux":
                    self.runbg("tracelog.exe -stop aux", os.getenv('PROGRAMFILES(X86)'))
            else:
                if mode == "Tee":
                    self.runbg("tracelog.exe -stop tee", os.getenv('PROGRAMFILES'))
                elif mode == "SPD":
                    self.runbg("tracelog.exe -stop spd", os.getenv('PROGRAMFILES'))
                elif mode == "gsc":
                    self.runbg("tracelog.exe -stop gsc", os.getenv('PROGRAMFILES'))
                elif mode == "_aux":
                    self.runbg("tracelog.exe -stop aux", os.getenv('PROGRAMFILES'))

            files = itertools.chain(glob.glob(r"C:\Windows\System32\LogFiles\WMI\*.etl.*"))
            
            tgtdir = pjoin(self.logdir, outname)
            self.mkdir(tgtdir)
            for src in files:
                self.move(src, tgtdir)

    def csme_bsod(self, mode="Tee", outname=""):
        logging.info(f"Running MEI driver BSOD/System Hang {mode} boot trace...")

        """ Delete registry if exist to avoid setting mix up """
        if mode == "Tee":
            self.runbg(r"reg delete HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\Tee /f", ".")
        elif mode == "SPD":
            self.runbg(r"reg delete HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\Spd /f", ".")
        elif mode == "gsc":
            self.runbg(r"reg delete HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\Gsc /f", ".")
        elif mode == "_aux":
            self.runbg(r"reg delete HKLM\SYSTEM\CurrentControlSet\Control\WMI\Autologger\Aux /f", ".")
        
        """"""
        meitemp = pjoin(self._tmp_dir, "CSME", "MEI", f'{mode}')

        mode = "aux" if mode == "_aux" else mode 

        """Now execute required files"""
        reg = f"trace_enable_{mode}_In_dmp.reg"

        self.runbg(reg, meitemp)
        
        messagebox.showwarning(title="trace running...", 
            message="You have enabled trace that requires a restart. Restart system and then reproduce your issue(s) if required. After BSOD is reproduced, the log will be stored in complete memory dump file.")

    def storage(self, outname="storage_trace"):
        logging.info("Running Intel Storage Trace...")
        
        rsttemp = pjoin(self._tmp_dir, "RST")

        self.runbg("IntelMAS.exe start -scan Logs -intelssd", rsttemp)

        logging.info('Success. Moving files...')
        tgtdir = pjoin(self.logdir, outname)
        self.mkdir(tgtdir)

        files = itertools.chain(glob.glob(fr"{rsttemp}/output/*/*"))
        for src in files:
            self.move(src, tgtdir)
        