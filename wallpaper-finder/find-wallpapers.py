import ast
import os
import shutil
from pathlib import Path

from common import MediaMetaData, CommonUtils
from common.CommonUtils import FileScanner

_logger = CommonUtils.get_logger("find-wallpapers")


def _get_activity_log_file(copy_dir_name) -> str:
    return f"{copy_dir_name}{os.path.sep}processed.log"


def _load_activity_log(copy_dir_name) -> set:
    activity_file = Path(_get_activity_log_file(copy_dir_name))
    if activity_file.exists() and activity_file.is_file():
        history = activity_file.read_text()
        return set() if history == str(set()) or history == "" else ast.literal_eval(history)
    return set()


def _save_activity_log(copy_dir_name, activity_log):
    with open(_get_activity_log_file(copy_dir_name), 'w') as f:
        f.write(str(activity_log))


def _copy_wallpaper(file, copy_dir_name):
    """
    Will copy file from source to destination if it's a wallpaper candidate
    :param file:
    :param copy_dir_name:
    :return:
    """
    if not (".jp" in file.lower() or "*.pn" in file.lower()):
        return False

    file_path = Path(file)
    dest_file = Path(copy_dir_name) / file_path.name
    details = MediaMetaData.get_metadata(file)
    geometry = details[MediaMetaData.MetaDataFields.geometry]
    width = float(geometry[0:geometry.find("x")])
    height = float(geometry[geometry.find("x") + 1:geometry.find("+")])
    ratio = width / height
    if 1.3 < ratio < 1.7 and width >= 2300:
        _logger.info(f"{file} is likely a wallpaper. Copying to {copy_dir_name}")
        shutil.copy2(file, dest_file)
        return True
    return False


def find_wallpapers(find_dir_name, copy_dir_name):
    """
    Copies files recursively from source to destination if it's a wallpaper candidate
    :param find_dir_name:
    :param copy_dir_name:
    :return:
    """
    activity_log = _load_activity_log(copy_dir_name)
    _logger.debug("Begin Scan Files")
    file_scanner = FileScanner([find_dir_name], is_qfiles=False, recurse=True)
    _logger.debug("Scan Files complete")
    counter = 0
    try:
        for file in file_scanner.files:
            # Optimization. If the file has been previously read, skip it
            if file in activity_log:
                _logger.warning(f"{file} has been processed before. Skipping...")
                continue
            # Optimization. If the file is in destination already skip it
            file_path = Path(file)
            dest_file = Path(copy_dir_name) / file_path.name
            if dest_file.exists():
                _logger.warning(f"{str(dest_file)} is already in the destination. Skipping this file")
                continue

            try:
                if not _copy_wallpaper(file, copy_dir_name):
                    _logger.debug(f"{file} is not a wallpaper")
            except Exception:
                _logger.exception(f"An Error occured while processing {file}.")

            activity_log.add(file)
            counter += 1
            if counter % 500 == 0:
                _logger.info("Saving Activity Log...")
                _save_activity_log(copy_dir_name, activity_log)
                _logger.info(f"Processed {counter} files thus far.")
    finally:
        _save_activity_log(copy_dir_name, activity_log)


if __name__ == "__main__":
    find_wallpapers("/.../.../SOURCE.../", "/.../DESTINATION...")
