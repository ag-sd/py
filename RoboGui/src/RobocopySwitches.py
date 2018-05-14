allSwitches = {
    "Source": {
        "/S": "Copy Sub folders",
        "/E": "Copy Subfolders, including Empty Subfolders.",
        # "/SEC": "Copy files with SECurity (equivalent to /COPY:DATS).",
        # "/DCOPY:T": "Copy Directory Timestamps.",
        # "/COPYALL": "Copy ALL file info (equivalent to /COPY:DATSOU).",
        "/NOCOPY": "Copy NO file info (useful with /PURGE).",
        "/A": "Copy only files with the Archive attribute set.",
        "/M": "Copy only files with the Archive attribute set,\n"
              "and also remove Archive attribute from source files.",
        # "/FFT": "Assume FAT File Times (2-second date/time granularity).",
        "/256": "Turn off very long path (> 256 characters) support.",
        "/LEV:n": "Only copy the top n LEVels of the source tree.",
        "/MAXAGE:n": "MAXimum file AGE - exclude files older than n days/date.",
        "/MINAGE:n": "MINimum file AGE - exclude files newer than n days/date.\n"
                     "(If n < 1900 then n = no of days, else n = YYYYMMDD date).",
    },
    "Copy": {
        "/L": "List only - don’t copy, timestamp or delete any files.",
        "/MOV": "MOVe files (delete from source after copying).",
        # "/MOVE": "Move files and dirs (delete from source after copying).",
        "/sl": "Copy symbolic links instead of the target.",
        "/Z": "Copy files in restartable mode (survive network glitch).",
        "/B": "Copy files in Backup mode.",
        "/J": "Copy using unbuffered I/O (recommended for large files). \n"
              "(Only in Windows 8 and Windows 10)",
        # "/NOOFFLOAD": "Copy files without using the Windows Copy Offload mechanism. \n
        # (Only in Windows 8 and Windows 10)",
        "/ZB": "Use restartable mode; if access denied use Backup mode.",
        # "/TBD": "Wait for sharenames To Be Defined (retry error 67).",
        # "/IPG:n": "Inter-Packet Gap (ms), to free bandwidth on slow lines.",
        "/R:n": "Number of Retries on failed copies - default is 1 million.",
        "/W:n": "Wait time between retries - default is 30 seconds.",
        # "/REG": "Save /R:n and /W:n in the Registry as default settings."
    },
    "Destination": {
        # "/A+:[RASHCNET]": "Set file Attribute(s) on destination files + add.",
        # "/A-:[RASHCNET]": "UnSet file Attribute(s) on destination files - remove.",
        "/FAT": "Create destination files using 8.3 FAT file names only.",
        "/CREATE": "CREATE directory tree structure + zero-length files only.",
        "/DST": "Compensate for one-hour DST time differences.",
        "/PURGE": "Delete destination files/folders that no longer exist in source. (Purge)",
        "/MIR": "MIRror a directory tree - equivalent to PURGE plus copy all sub folders"
    },
    "Logging": {
        "/L": "List only - don’t copy, timestamp or delete any files.",
        "/NP": "No Progress - don’t display % copied.",
        # "/unicode": "Display the status output as Unicode text. Since Windows 7",
        # "/TS": "Include Source file Time Stamps in the output.",
        "/FP": "Include Full Pathname of files in the output.",
        "/NS": "No Size - don’t log file sizes.",
        # "/NC": "No Class - don’t log file classes.",
        "/NFL": "No File List - don’t log file names.",
        "/NDL": "No Directory List - don’t log directory names.",
        "/TEE": "Output to console window, as well as the log file.",
        # "/NJH": "No Job Header.",
        # "/NJS": "No Job Summary.",
        "/LOG:file": "Log File (overwrite)\t",
        "/LOG+:file": "Log File (append)\t",
        "/UNILOG:file": "Unicode Log file (overwrite)\t",
        "/UNILOG+:file": "Unicode Log file (append)\t"
    },
    "Advanced": {
        "/XO": "Exclude Older - if destination file exists and is the same date \n"
               "or newer than the source - don’t bother to overwrite it.",
        "/XC": "Exclude Changed files",
        "/XN": "Exclude Newer files",
        "/XL": "Exclude 'Lonely' files and directories (present in source but not \n"
               "destination). This will prevent any new files being added to the destination.",
        "/XX": "Exclude 'Extra' files and directories (present in destination but not \n"
               "source). This will prevent any deletions from the destination. (this is the default)",
        "/MT:n": "Multithreaded copying, n = no. of threads to use (1-128) default = 8 threads. \n"
                 "Since Windows 7."
    }
}
