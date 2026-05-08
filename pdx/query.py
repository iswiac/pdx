# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 The PDX Project Authors

from pdx.model import Model
from pdx.qdrant import VDB

import logging
import os
import shlex
import shutil
import subprocess
import tempfile

from typing import Optional


class QueryHandler:
    model: Model
    vdb: VDB
    limit: int
    min_score: float
    viewer: Optional[str]

    def __init__(self, cname: str, limit: int, min_score: float, viewer: Optional[str]):
        self.model = Model(force_cpu=True)
        self.vdb = VDB(cname=cname)
        self.limit = limit
        self.min_score = min_score
        self.viewer = viewer

    def query(self, query_str: str) -> None:
        vector = self.model.prompt_to_vector(query_str)
        results = self.vdb.query_photos(vector, self.limit, self.min_score)
        if not results:
            logging.warning(f"no photos matched by the query: {query_str}")
            return

        if self.viewer is None:
            # print the results to stdout
            for i, (score, path, desc) in enumerate(results, start=1):
                print(f"{i:04}\t{score:.6f}\t[{desc}]\t{path}")
            return

        # create symlinks in a temp directory and run a viewer on it
        temp_dir = tempfile.mkdtemp()
        try:
            for i, (score, path, desc) in enumerate(results, start=1):
                path_part = path.replace("/", "-").lstrip("-")
                linkname = f"{i:04}-{score:.6f}-{path_part}"
                dest = os.path.join(temp_dir, linkname)
                os.symlink(os.path.abspath(path), dest)
            cmd = shlex.split(self.viewer) + [temp_dir]
            logging.info(f"executing: {cmd}")
            subprocess.run(cmd)
        finally:
            logging.info(f"removing: {temp_dir}")
            shutil.rmtree(temp_dir, ignore_errors=True)
