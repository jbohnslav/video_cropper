import numpy as np
import cv2
from typing import Union
from .file_io import VideoReader, VideoWriter
import os
from tqdm import tqdm

def crop(image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
    assert image.ndim > 1
    return image[y:y + h, x:x + w, ...]


def crop_video(infile: Union[str, os.PathLike],
               outfile: Union[str, os.PathLike],
               x: int,
               y: int,
               w: int,
               h: int,
               movie_format: str = 'ffmpeg'):
    with VideoReader(infile) as reader:
        with VideoWriter(outfile, movie_format=movie_format, asynchronous=False) as writer:
            for frame in tqdm(reader):
                writer.write(crop(frame, x, y, w, h))