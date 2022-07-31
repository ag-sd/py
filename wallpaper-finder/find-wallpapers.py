import os
import shutil

import MediaMetaData
from CommonUtils import FileScanner


def find_wallpapers(find_dir_name, copy_dir_name):
    """
    Copies files recursively from source to destination if it's a wallpaper candidate
    :param find_dir_name:
    :param copy_dir_name:
    :return:
    """
    file_scanner = FileScanner([find_dir_name], is_qfiles=False, recurse=True)
    for file in file_scanner.files:
        if ".jp" in file.lower() or "*.pn" in file.lower():
            # Optimization. If the file is in destination already skip it
            _, file_name = os.path.split(file)
            dest_file = f"{copy_dir_name}{os.path.sep}{file_name}"
            if os.path.exists(dest_file):
                print(f"{file_name} is already in the destination. Skipping this file")
                continue

            details = MediaMetaData.get_metadata(file)
            geometry = details[MediaMetaData.MetaDataFields.geometry]
            width = float(geometry[0:geometry.find("x")])
            height = float(geometry[geometry.find("x") + 1:geometry.find("+")])
            ratio = width / height
            if 1.3 < ratio < 1.7 and width >= 2300:
                print(f"{file} is likely a wallpaper. Copying to {copy_dir_name}")
                shutil.copy2(file, dest_file)


if __name__ == "__main__":
    find_wallpapers("/.../.../SOURCE.../", "/.../DESTINATION...")
