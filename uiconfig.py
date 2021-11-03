r"""
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
"""

ISSUETYPES = {
  "Graphics related": {
  	"tip": "",
    "ingredients": [6,21,13,14],
    "default": [],
    "exclusive": [6,21,13,14]
  },
  "BIOS related": {
  	"tip": "",
    "ingredients": [4,9],
    "default": [4,9],
    "exclusive": []
  },
  "Thunderbolt related": {
  	"tip": "",
    "ingredients": [8,15],
    "default": [],
    "exclusive": [8,15]
  },
  "Live Dump File": {
  	"tip": "",
    "ingredients": [10],
    "default": [10],
    "exclusive": []
  },
  "Storage related": {
  	"tip": "",
    "ingredients": [10,12,16,35],
    "default": [10,12,16,35],
    "exclusive": []
  },
  "System Performance": {
  	"tip": "",
    "ingredients": [2],
    "default": [2],
    "exclusive": []
  },
  "Audio related": {
  	"tip": "",
    "ingredients": [17],
    "default": [17],
    "exclusive": []
  },
  "I2C": {
  	"tip": "",
    "ingredients": [18,20],
    "default": [],
    "exclusive": [18,20]
  }, 
  "CSME": {
    "tip": "", 
    "ingredients": [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34], 
    "default": [], 
    "exclusive": [[27, 31], [28, 32], [29, 33], [30, 34]]
  }
}

AVAILABLE = [1, 2, 3, 4, 6, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]

INGREDIENTS = {
  "N/A": {
    "id": -99,
    "type": "",
    "reboot": False,
    "tip": ""
  },
  "USB": {
    "id": 1,
    "type": "trace",
    "reboot": False,
    "tip": ""
  },
  "High Loading Activities": {
    "id": 2,
    "type": "trace",
    "reboot": False,
    "tip": ""
  },
  "Idle ETL": {
    "id": 3,
    "type": "trace",
    "reboot": False,
    "tip": ""
  },
  "ACPI Code dump": {
    "id": 4,
    "type": "config",
    "reboot": False,
    "tip": ""
  },
  "Unexpected Reset": {
    "id": 5,
    "type": "log",
    "reboot": False,
    "tip": ""
  },
  "Display": {
    "id": 6,
    "type": "trace",
    "reboot": False,
    "tip": "ETL trace tool"
  },
  "SLP_S0 Status": {
    "id": 7,
    "type": "log",
    "reboot": False,
    "tip": ""
  },
  "TBT (S0/S3/S4)": {
    "id": 8,
    "type": "trace",
    "reboot": False,
    "tip": ""
  },
  "Runtime ACPI Code": {
    "id": 9,
    "type": "trace",
    "reboot": False,
    "tip": ""
  },
  "Live Dump File": {
    "id": 10,
    "type": "trace",
    "reboot": False,
    "tip": ""
  },
  "RST Logs": {
    "id": 12,
    "type": "log",
    "reboot": False,
    "tip": ""
  },
  "Video/performance": {
    "id": 13,
    "type": "trace",
    "reboot": False,
    "tip": "GPUView tool"
  },
  "Realtime BSOD": {
    "id": 14,
    "type": "trace",
    "reboot": True,
    "tip": ""
  },
  "TBT (boot)": {
    "id": 15,
    "type": "trace",
    "reboot": True,
    "tip": ""
  },
  "Optane Logs": {
    "id": 16,
    "type": "log",
    "reboot": False,
    "tip": ""
  },
  "ISST": {
    "id": 17,
    "type": "trace",
    "reboot": True,
    "tip": ""
  },
  "I2C": {
    "id": 18,
    "type": "trace",
    "reboot": True,
    "tip": ""
  },
  "System Information": {
    "id": 19,
    "type": "config",
    "reboot": False,
    "tip": "Collect system information and event log."
  },
  "I2C ACPI": {
    "id": 20,
    "type": "trace",
    "reboot": True,
    "tip": ""
  },
  "Boot Trace": {
    "id": 21,
    "type": "trace",
    "reboot": True, 
    "tip": ""
  },
  "Wiman Driver Log": {
    "id": 22, 
    "type": "trace", 
    "reboot": True, 
    "tip": ""
  },
  "Installer Log": {
    "id": 23, 
    "type": "log", 
    "reboot": False,
    "tip": ""
  },
  "LMS Driver Log": {
    "id": 24, 
    "type": "log",
    "reboot": False,
    "tip": ""
  }, 
  "iCLS Driver Log": {
    "id": 25, 
    "type": "log",
    "reboot": False,
    "tip": ""
  },
  "DAL Driver Log": {
    "id": 26, 
    "type": "trace",
    "reboot": True,
    "tip": ""
  },
  "MEI Driver Yellow Bang": {
    "id": 27, 
    "type": "trace",
    "reboot": True,
    "tip": ""
  },
  "SPD Driver Yellow Bang": {
    "id": 28, 
    "type": "trace",
    "reboot": True,
    "tip": ""
  },
   "GSC Driver Yellow Bang": {
    "id": 29, 
    "type": "trace",
    "reboot": True,
    "tip": ""
  },
  "AUX Driver Yellow Bang": {
    "id": 30, 
    "type": "trace",
    "reboot": True,
    "tip": ""
  },
  "MEI Driver BSOD/System Hang": {
    "id": 31, 
    "type": "trace",
    "reboot": False,
    "tip": ""
  },
  "SPD Driver BSOD/System Hang": {
    "id": 32, 
    "type": "trace",
    "reboot": False,
    "tip": ""
  },
  "GSC Driver BSOD/System Hang": {
    "id": 33, 
    "type": "trace",
    "reboot": False,
    "tip": ""
  },
  "AUX Driver BSOD/System Hang": {
    "id": 34, 
    "type": "trace",
    "reboot": False,
    "tip": ""
  },
  "Intel Storage Trace": {
    "id": 35, 
    "type": "trace",
    "reboot": False,
    "tip": ""
  }
}