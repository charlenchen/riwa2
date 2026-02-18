from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import os
import base64
from src.utils.logger import logger


@dataclass
class ImageGeneration:
    """Represents a generated image."""
    prompt: str
    image_path: Optional[str] = None
    image_data: Optional[bytes] = None
    style: str = "default"
    width: int = 512
    height: int = 512
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            'prompt': self.prompt,
            'image_path': self.image_path,
            'style': self.style,
            'width': self.width,
            'height': self.height,
            'metadata': self.metadata,
            'created_at': self.created_at
        }

    def save(self, filepath: Optional[str] = None) -> Optional[str]:
        """Save image to file."""
        if self.image_data:
            path = filepath or self.image_path or f"data/snapshots/image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(self.image_data)
            self.image_path = path
            logger.info(f"Image saved to {path}")
            return path
        return None


class Illustrator:
    """
    Text-to-image interface for generating illustrations from story content.
    Supports multiple backends (API-based or local models).
    """

    def __init__(
        self,
        output_dir: str = "data/snapshots/illustrations",
        api_client: Optional[Any] = None,
        default_style: str = "digital_art"
    ):
        self.output_dir = output_dir
        self.api_client = api_client
        self.default_style = default_style
        self._generations: List[ImageGeneration] = []

        os.makedirs(output_dir, exist_ok=True)

        # Style presets for prompt enhancement
        self.style_presets = {
            'digital_art': "digital art, highly detailed, vibrant colors",
            'watercolor': "watercolor painting, soft edges, artistic",
            'oil_painting': "oil painting, textured, classical art style",
            'anime': "anime style, cel shaded, vibrant",
            'realistic': "photorealistic, highly detailed, 8k",
            'pixel_art': "pixel art, retro game style, 16-bit",
            'sketch': "pencil sketch, black and white, hand drawn",
            'cyberpunk': "cyberpunk style, neon lights, futuristic, dark atmosphere",
            'fantasy': "fantasy art, magical, ethereal lighting"
        }

    def generate_image(
        self,
        prompt: str,
        style: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        save: bool = True
    ) -> Optional[ImageGeneration]:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the image
            style: Art style preset or custom style
            width: Image width in pixels
            height: Image height in pixels
            save: Whether to save the image to disk

        Returns:
            ImageGeneration object or None if failed
        """
        style = style or self.default_style

        # Enhance prompt with style preset
        enhanced_prompt = self._enhance_prompt(prompt, style)

        logger.info(f"Generating image: {enhanced_prompt[:50]}...")

        # Generate using API client or placeholder
        if self.api_client:
            generation = self._generate_with_api(
                enhanced_prompt, style, width, height
            )
        else:
            generation = self._generate_placeholder(
                enhanced_prompt, style, width, height
            )

        if generation and save:
            generation.save()

        if generation:
            self._generations.append(generation)

        return generation

    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance prompt with style keywords."""
        style_keywords = self.style_presets.get(style, style)
        return f"{prompt}, {style_keywords}, high quality, detailed"

    def _generate_with_api(
        self,
        prompt: str,
        style: str,
        width: int,
        height: int
    ) -> Optional[ImageGeneration]:
        """Generate image using API client."""
        try:
            # Expected API: client.generate(prompt, width, height, **kwargs)
            result = self.api_client.generate(
                prompt=prompt,
                width=width,
                height=height,
                style=style
            )

            if hasattr(result, 'image_data'):
                image_data = result.image_data
            elif isinstance(result, bytes):
                image_data = result
            elif isinstance(result, dict) and 'data' in result:
                image_data = base64.b64decode(result['data'])
            else:
                logger.error(f"Unknown API result format: {type(result)}")
                return None

            return ImageGeneration(
                prompt=prompt,
                image_data=image_data,
                style=style,
                width=width,
                height=height,
                metadata={'source': 'api'}
            )
        except Exception as e:
            logger.error(f"API image generation failed: {e}")
            return None

    def _generate_placeholder(
        self,
        prompt: str,
        style: str,
        width: int,
        height: int
    ) -> ImageGeneration:
        """Generate a placeholder image when no API is available."""
        # Create a simple SVG placeholder
        svg_content = self._create_svg_placeholder(prompt, style, width, height)

        return ImageGeneration(
            prompt=prompt,
            image_data=svg_content.encode('utf-8'),
            style=style,
            width=width,
            height=height,
            metadata={
                'source': 'placeholder',
                'note': 'No image API configured. Replace with actual image generation.'
            }
        )

    def _create_svg_placeholder(
        self,
        prompt: str,
        style: str,
        width: int,
        height: int
    ) -> str:
        """Create an SVG placeholder image."""
        # Truncate prompt for display
        display_prompt = prompt[:60] + "..." if len(prompt) > 60 else prompt

        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1a1a2e;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#16213e;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#bg)"/>
  <text x="50%" y="45%" text-anchor="middle" fill="#e94560" font-size="24" font-family="Arial">
    [Image Placeholder]
  </text>
  <text x="50%" y="55%" text-anchor="middle" fill="#ffffff" font-size="14" font-family="Arial">
    Style: {style}
  </text>
  <text x="50%" y="70%" text-anchor="middle" fill="#aaaaaa" font-size="12" font-family="Arial">
    {display_prompt}
  </text>
</svg>'''
        return svg

    def generate_scene_illustration(
        self,
        story_segment: Any,
        style: Optional[str] = None
    ) -> Optional[ImageGeneration]:
        """
        Generate an illustration for a story segment.

        Args:
            story_segment: StorySegment to illustrate
            style: Art style

        Returns:
            Generated image or None
        """
        # Extract key elements for the prompt
        events = story_segment.metadata.get('events', [])
        characters = story_segment.metadata.get('characters', [])

        # Build illustration prompt
        if 'attack' in events or 'combat' in events:
            scene_type = "intense battle scene"
        elif 'interact' in events:
            scene_type = "character interaction"
        elif 'character_added' in events:
            scene_type = "character introduction"
        else:
            scene_type = "narrative scene"

        character_desc = " featuring " + ", ".join(characters) if characters else ""

        prompt = f"{scene_type}{character_desc}, {story_segment.summary}"

        return self.generate_image(prompt, style=style)

    def generate_character_portrait(
        self,
        character: Any,
        style: Optional[str] = None
    ) -> Optional[ImageGeneration]:
        """
        Generate a character portrait.

        Args:
            character: Character entity
            style: Art style

        Returns:
            Generated portrait or None
        """
        name = getattr(character, 'name', 'Unknown')
        description = getattr(character, 'description', '')
        attributes = getattr(character, 'attributes', {})

        # Build portrait prompt
        prompt_parts = [f"Portrait of {name}"]

        if description:
            prompt_parts.append(description)

        # Add attribute-based descriptors
        if attributes.get('power', 0) > 80:
            prompt_parts.append("powerful aura")
        if attributes.get('speed', 0) > 80:
            prompt_parts.append("agile appearance")
        if attributes.get('magic', 0) > 80:
            prompt_parts.append("mystical energy")

        prompt = ", ".join(prompt_parts)

        return self.generate_image(prompt, style=style or "fantasy")

    def get_generations(self, limit: int = 10) -> List[ImageGeneration]:
        """Get recent image generations."""
        return self._generations[-limit:]

    def export_gallery(self, filepath: str) -> bool:
        """
        Export an HTML gallery of generated images.

        Args:
            filepath: Output HTML file path

        Returns:
            True if successful
        """
        try:
            html_content = self._generate_html_gallery()
            with open(filepath, 'w') as f:
                f.write(html_content)
            logger.info(f"Gallery exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export gallery: {e}")
            return False

    def _generate_html_gallery(self) -> str:
        """Generate HTML gallery content."""
        images_html = ""
        for gen in self._generations:
            if gen.image_path:
                images_html += f'''
                <div class="image-card">
                    <img src="{gen.image_path}" alt="{gen.prompt[:50]}">
                    <p class="prompt">{gen.prompt}</p>
                    <p class="meta">{gen.style} | {gen.width}x{gen.height}</p>
                </div>'''

        return f'''<!DOCTYPE html>
<html>
<head>
    <title>RIW2 Image Gallery</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }}
        h1 {{ text-align: center; color: #e94560; }}
        .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
        .image-card {{ background: #16213e; border-radius: 8px; overflow: hidden; }}
        .image-card img {{ width: 100%; height: 300px; object-fit: cover; }}
        .prompt {{ padding: 10px; font-size: 14px; color: #aaa; }}
        .meta {{ padding: 0 10px 10px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <h1>RIW2 Illustration Gallery</h1>
    <div class="gallery">{images_html}</div>
</body>
</html>'''
