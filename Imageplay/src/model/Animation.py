from PyQt5 import QtGui

import Imageplay


class AnimationHandler:

    def __init__(self, animation_file):
        self.animation_file = animation_file
        self.movie = QtGui.QMovie(animation_file)
        self.current_frame = 0

    def next_frame(self):
        Imageplay.logger.info("Current frame is " +
                              str(self.current_frame) + "/" +
                              str(self.movie.frameCount()))
        self.movie.jumpToFrame(self.current_frame)
        self.current_frame += 1
        return self.movie.currentImage()

    def has_next(self):
        return self.current_frame < self.movie.frameCount()

    def prev_frame(self):
        if self.current_frame == 0:
            return self.movie.currentPixMap
        else:
            self.current_frame -= 1
            return self.next_frame()
