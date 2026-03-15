# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 The PDX Project Authors

import logging
import os

from pathlib import Path


PHOTOS_EXTS = ("heic", "heif", "jpeg", "jpg", "png")


class Finder:
    _include_symlinks: bool
    _photos: list[str]

    def __init__(self, include_symlinks: bool = False):
        self._include_symlinks = include_symlinks
        self._photos = []

    @property
    def photos(self) -> list[str]:
        return self._photos

    def find_photos_in_dir(self, path: Path) -> None:
        for dir_name, _, files in os.walk(path):
            for f in files:
                _, ext = os.path.splitext(f)
                if not ext:
                    # no file extension
                    continue

                if ext[1:].lower() not in PHOTOS_EXTS:
                    # not a supported extension
                    continue

                abs_path = Path(dir_name) / f
                if not self._include_symlinks and abs_path.is_symlink():
                    continue

                self._photos.append(str(abs_path))

    def handle_path(self, path: Path) -> None:
        if path.is_file():
            # take regular files as photos to index
            self._photos.append(str(path))
        elif path.is_dir():
            # traverse directories recursively and look for files matching PHOTOS_EXTS
            self.find_photos_in_dir(path)
        else:
            logging.warning(f"unhandled argument: {path}")


def find_photos(paths: tuple[str, ...], include_symlinks: bool = False) -> list[str]:
    finder = Finder(include_symlinks)

    for arg in paths:
        path = Path(arg)
        finder.handle_path(path)

    return finder.photos
