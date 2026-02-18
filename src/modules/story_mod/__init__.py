"""
RIW2 Story Module

Story generation and illustration.
"""

from src.modules.story_mod.narrator import Narrator, StorySegment
from src.modules.story_mod.illustrator import Illustrator, ImageGeneration

__all__ = [
    "Narrator",
    "StorySegment",
    "Illustrator",
    "ImageGeneration"
]
