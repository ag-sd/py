# # https://medium.com/learning-the-go-programming-language/calling-go-functions-from-other-languages-4c7d8bcc69bf
# # https://gist.github.com/helinwang/4f287a52efa4ab75424c01c65d77d939

from ctypes import *
from ctypes import c_char_p
from datetime import datetime

import imagehash
from PIL import Image

lib = cdll.LoadLibrary("/mnt/Stuff/go/imagehash/imagehash.so")


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
    "/mnt/Stuff/test/0266554465.jpeg",
    "/mnt/Stuff/test/09_Spot-the-Difference-1 (copy).jpg",
    "/mnt/Stuff/test/09_Spot-the-Difference-1.jpg",
    "/mnt/Stuff/test/1animated_Test_image.gif",
    "/mnt/Stuff/test/1_XdqiA-pdkeFuX5W2-NSaNg.jpeg",
    "/mnt/Stuff/test/1_XdqiA-pdkeFuX5W2-NSaNg1.jpeg",
    "/mnt/Stuff/test/20190121_140646506_iOS.jpg",
    "/mnt/Stuff/test/dir1/20180313_175523756_iOS.jpg",
    "/mnt/Stuff/test/dir1/20180706_235102478_iOS.jpg",
    "/mnt/Stuff/test/dir1/20180716_125622752_iOS.jpg",
    "/mnt/Stuff/test/dir1/20190104_191345504_iOS.jpg",
    "/mnt/Stuff/test/dir1/ajax-loader.gif",
    "/mnt/Stuff/test/dir1/BLG_Andrew-G.-River-Sample_09.13.12.png",
    "/mnt/Stuff/test/dir1/dir2/1_XdqiA-pdkeFuX5W2-NSaNg.jpeg",
    "/mnt/Stuff/test/dir1/dir2/20180720_225906000_iOS.png",
    "/mnt/Stuff/test/dir1/dir2/20180810_024000463_iOS.jpg",
    "/mnt/Stuff/test/dir1/dir2/20190113_024653582_iOS.jpg",
    "/mnt/Stuff/test/dir1/dir2/dir3/20180810_024000463_iOS (copy).jpg",
    "/mnt/Stuff/test/dir1/dir2/dir3/20180810_024000463_iOS.jpg",
    "/mnt/Stuff/test/dir1/dir2/dir3/d/20180810_024000463_iOS.jpg",
    "/mnt/Stuff/test/dir1/ff_x20_008.JPG",
    "/mnt/Stuff/test/dir1/image (copy).jpeg",
    "/mnt/Stuff/test/dir1/image.jpeg",
    "/mnt/Stuff/test/dir1/images.jpeg",
    "/mnt/Stuff/test/dir1/spongebob (copy).jpeg",
    "/mnt/Stuff/test/ff x20_008.JPG",
    "/mnt/Stuff/test/image.jpeg",
    "/mnt/Stuff/test/maxresdefault (copy).jpg",
    "/mnt/Stuff/test/maxresdefault.jpg",
    "/mnt/Stuff/test/sample4_l.jpg",
    "/mnt/Stuff/test/sample_01.jpg",
    "/mnt/Stuff/test/spongebob (copy).jpeg",
    "/mnt/Stuff/test/spongebob.jpeg",
    "/mnt/Stuff/test/Spot_the_difference (copy).png",
    "/mnt/Stuff/test/Spot_the_difference.png"
]

algorithm = "aHash"
test_go = True
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