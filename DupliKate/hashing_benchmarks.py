# # https://medium.com/learning-the-go-programming-language/calling-go-functions-from-other-languages-4c7d8bcc69bf
# # https://gist.github.com/helinwang/4f287a52efa4ab75424c01c65d77d939

from ctypes import *
from ctypes import c_char_p
from datetime import datetime

import imagehash
from PIL import Image

lib = cdll.LoadLibrary("[redacted]imagehash.so")


class GoString(Structure):
    _fields_ = [("p", c_char_p), ("n", c_longlong)]


def _string_to_go(string):
    return GoString(string.encode('utf-8'), len(string))


lib.GetHashFromImageFile.argtypes = [GoString, GoString]
lib.GetHashFromImageFile.restype = c_longlong


def get_go_hash(file_name, algorithm):
    file = _string_to_go(file_name)
    algo = _string_to_go(algorithm)
    return lib.GetHashFromImageFile(file, algo)


def get_python_hash(file_name, algorithm):
    image = Image.open(file_name)
    if algorithm == "aHash":
        return imagehash.average_hash(image)
    elif algorithm == "dHash":
        return imagehash.dhash(image)
    elif algorithm == "pHash":
        return imagehash.phash(image)
    else:
        return -1


test_files = [
    # redacted
]

algorithm = "aHash"
test_go = False
counter = 0
start_time = datetime.now()
for i in range(0, 10):
    print(f"Starting frame {i}")
    frame_start = datetime.now()
    for _file in test_files:
        counter += 1
        if test_go:
            get_go_hash(_file, algorithm)
        else:
            get_python_hash(_file, algorithm)
    print(f"Frame completed in {(datetime.now() - frame_start).total_seconds()} seconds")
print(f"Test completed in {(datetime.now() - start_time).total_seconds()} seconds for {counter} files")

"""
Total of 350 files
        Go  	    Python
aHash	42.69919	16.41857
dhash	42.972374	17.908552
pHash	45.985559	17.575515
"""