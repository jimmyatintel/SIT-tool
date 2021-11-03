# Software Issue Tracer (SIT)
## Dependencies
- pillow (PIL): `pip install pillow`
- psutil: `pip install psutil`
- trace scripts (included)

## Usage
### Developer
When developing, run your python interpreter (e.g. powershell.exe) as administrator to avoid permission error.
```cmd
python .\UI.py
```
Inside `settings.ini` enable debug mode to avoid resource path errors.
```
[General]
debug = True
```
### User
- See `SIT-QuickGuide-V1.2.2.docx` for instructions on how to use this tool.

## Build & Release
Building requires `pyinstaller`. Run `pip install pyinstaller` to install or [here](https://www.pyinstaller.org/) for more info.

1. Build executable package at `dist\UI\`
    ```cmd
    pyinstaller .\UI.py
    ```
2. Automatic compression to `release\SITyyyyMMdd.zip`
    ```cmd
    powershell.exe autozip.ps1
    ```
3. Upload to folder instructed by Jet.

## Changelog
- 7/8/19 - converted to python. integrated into the bsod_offline environment.
- 7/15/19 - updated GUI. added TBT traces.
- 7/16/19 - fixed banner and copyright label geometry issues.
- 7/17/19 - implemented splash screen using batch. fixed splash screen white  flash.
- 8/5/19 - Added Gfx & TBT traces. Changed to dynamic created scripts.
- 8/22/19 - Added Storage related traces. Added unexpected reset traces. Added handling of boot traces. First standalone version.
- 9/3/19 - fixed bug with whitespace in path. Changed naming & added "collect all" buttons
- 9/27/19 - added function for quicklaunch. added icons. removed many options. updated display & video trace.
- 10/9/19 - added system info collection. changed to directly run scripts are rsrc directory. Added achi dump for bios related.
- 10/15/19 - fixed live dump file trace. changed cancel button to clear user options.
- 10/18/19 - Added high loading activities, detecting non-Intel cpu,  zipfile creation, log folder format change.
- 10/25/19 - adjusted UI. added option for toggling zipfile creation in settings.ini
- 10/30/19 - Added program logging. Added prompt to decide whether to run sysinfo.
- 11/20/19 - Added runtime acpi code dump. Removed windbg button.
- 12/27/19 - Moved system info to optional.
- 1/3/20 - Added detection of testsigning before running ACPI. Added user guide.
- 1/21/20 - Added realtime bsod trace for graphics related issue.
Added live dump to storage related. I2C ACPI.
Added default ingredients.
Added prompt for timeout for high loading activities.
- 4/6/20 - Update Gfx scripts
- 4/20/20 - Updated realtime BSOD (gfx) script.
- 5/29/20 - Updated isst scripts.
- 9/17/20 - Add Graphic boot trace.
- 10/28/20 - Add Wiman, DAL, iCLS, installer, LMS driver log trace.
- 10/30/20 - Add MEI driver log traces.
- 11/06/20 - Update Wiman driver log to boottrace.
- 11/16/20 - Add support for multiple boottraces running simultaneously.
- 11/20/20 - Rename MEI functions. Support pairwise self exclusive traces.
- 1/11/21 - Add registry reset button.

## Structure
### Files
- `dist\launch.bat`: Proxy launcher that first checks for administrator priviledge, then creates a splashscreen when the program is loading.
- `UI.py`: Responsible for the GUI and program flow.
- `uiconfig.py`: Configuration for issuetypes and ingredient traces.
- `tracers.py`: Implementation for each ingredient traces.

### uiconfig
##### Issue Type Structure
- `tip`: The description to show on the display when the cursor hovers above this issue type.
- `ingredients`: Each issue type links to 1 or more ingredient trace(s). 
- `default`: The ingredients that are selected by default. Others are optional.
- `exclusive`: Ingredients that cannot be selected together.
##### Ingredient Structure
- `id`: Unique id to identify the trace in `UI.py`
- `type`: One of `trace`,`log`,`config`
- `reboot`: If this trace involves a reboot (i.e. the tool would be closed, and should be re-launched to collect data).
- `tip`: The description to show on the display when the cursor hovers above this ingredient trace.

### tracers
For details on each trace, refer to documentation in `tracers.py`

### handling boot trace
Currently, boot traces are handled by setting a variable in settings.ini when enabling, then after rebooting and relaunching the tool, it will recognize boot trace based on the settings.ini. 