import argparse
import os
import pathlib
from typing import Union

import numpy as np
from tqdm import tqdm
from vidio import VideoReader, VideoWriter


def crop(image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
    assert image.ndim > 1
    return image[y:y + h, x:x + w, ...]


def crop_video(infile: Union[str, os.PathLike, pathlib.Path],
               outfile: Union[str, os.PathLike, pathlib.Path],
               x: int,
               y: int,
               w: int,
               h: int,
               movie_format: str = 'ffmpeg'):
    with VideoReader(infile) as reader:
        with VideoWriter(outfile, movie_format=movie_format, asynchronous=False, fps=reader.fps) as writer:
            # import pdb; pdb.set_trace()
            for frame in tqdm(reader):
                writer.write(crop(frame, x, y, w, h))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crop video')
    parser.add_argument('-i', '--infile', required=True, type=str,
                        help='file to read')
    parser.add_argument('-o', '--outfile', required=True, type=str,
                        help='filename of video to write')
    parser.add_argument('-x', required=True, type=int,
                        help='x coordinate of top-left corner')
    parser.add_argument('-y', required=True, type=int,
                        help='y coordinate of top-left corner')
    parser.add_argument('-w', required=True, type=int,
                        help='width')
    parser.add_argument('--height', required=True, type=int,
                        help='height')
    parser.add_argument('--movie_format', default='ffmpeg', type=str,
                        help='format of output movie. see vidio on github')
    args = parser.parse_args()
    # have to use --height instead of -h because -h means help
    crop_video(args.infile, args.outfile, args.x, args.y, args.w, args.height, args.movie_format)