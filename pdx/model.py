# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 The PDX Project Authors

import logging
import open_clip
import os
import torch

from collections.abc import Callable
from typing import Any, cast
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageFile

# tolerate truncated JPEGs to avoid `OSError: broken data stream when reading image file`
cast(Any, ImageFile).LOAD_TRUNCATED_IMAGES = True

# add support for HEIC/HEIF images if available
try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass


MODEL_NAME = "ViT-L-14"
PRETRAINED = "laion2b_s32b_b82k"


class Model:
    _device: str
    _model: torch.nn.Module
    _preproc: Callable
    _tokenizer: Callable

    def __init__(self, force_cpu: bool = False):
        # check whether CUDA acceleration is available
        self._device = "cuda" if not force_cpu and torch.cuda.is_available() else "cpu"

        # initialize model and preprocessor
        self._model, _, self._preproc = open_clip.create_model_and_transforms(
            model_name=MODEL_NAME,
            pretrained=PRETRAINED,
        )

        # get tokenizer
        self._tokenizer = open_clip.get_tokenizer(model_name=MODEL_NAME)

        # switch the model to inference mode
        self._model.eval()

        # move the model to the target device
        logging.info(f"{self.__class__.__name__}: using device: {self._device.upper()}")
        self._model.to(self._device)

    @property
    def device(self):
        return self._device

    def preprocess_img(self, file_path: str):
        img = Image.open(file_path).convert("RGB")
        return (file_path, self._preproc(img))

    def preprocess_img_batch(self, paths, pbar=None):
        results = []

        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            pool = {executor.submit(self.preprocess_img, p): p for p in paths}
            for t in as_completed(pool):
                if pbar is not None:
                    pbar.update(1)
                try:
                    results.append(t.result())
                except Exception as e:
                    logging.warning(f"Skipping {pool[t]}: {e}")

        return results

    def tensors_to_vectors(self, tensors):
        with torch.no_grad():
            st = torch.stack(tensors).to(self._device)
            encode_image_fn = cast(
                Callable[..., torch.Tensor], getattr(self._model, "encode_image")
            )
            tensor = encode_image_fn(st)
            return tensor.cpu().numpy()

    def prompt_to_vector(self, prompt):
        """Fixed: Moves tokens to GPU and results to CPU."""
        with torch.no_grad():
            # Move text tokens to the device (GPU)
            text = self._tokenizer([prompt]).to(self._device)
            encode_text_fn = cast(
                Callable[..., torch.Tensor], getattr(self._model, "encode_text")
            )
            # Move the resulting vector back to CPU
            vector = encode_text_fn(text)
            return vector.cpu().numpy().flatten().tolist()
