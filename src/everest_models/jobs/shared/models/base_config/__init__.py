from typing import TypeVar

from .base import ModelConfig, RootModelConfig

Model = TypeVar("Model", bound=ModelConfig)

__all__ = ["ModelConfig", "RootModelConfig", "Model"]
