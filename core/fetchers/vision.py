"""Vision analysis for image content extraction.

Analyzes images found in fetched URL content using vision models.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin


logger = logging.getLogger(__name__)


@dataclass
class VisionAnalysis:
    """Result of vision analysis.
    
    Attributes:
        image_url: The URL of the analyzed image.
        description: Text description of the image content.
        detected_text: Any text detected in the image (OCR).
        confidence: Confidence score of the analysis (0.0 to 1.0).
        metadata: Additional metadata about the analysis.
    """
    
    image_url: str
    description: str
    detected_text: str
    confidence: float
    metadata: dict[str, Any]
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VisionAnalyzer:
    """Analyzes images using vision models.
    
    Extracts text and descriptions from images found in web content.
    """
    
    def __init__(self, api_key: str | None = None):
        """Initialize vision analyzer.
        
        Args:
            api_key: Optional API key for vision service.
        """
        self.api_key = api_key
        
    async def analyze_images(
        self,
        html_content: str,
        base_url: str,
        max_images: int = 3
    ) -> list[VisionAnalysis]:
        """Extract and analyze images from HTML content.
        
        Args:
            html_content: The HTML content to parse.
            base_url: Base URL for resolving relative image URLs.
            max_images: Maximum number of images to analyze.
            
        Returns:
            List of VisionAnalysis results.
        """
        # Extract image URLs from HTML
        image_urls = self._extract_image_urls(html_content, base_url)
        
        if not image_urls:
            return []
        
        # Analyze images
        results = []
        for url in image_urls[:max_images]:
            analysis = await self._analyze_single_image(url)
            if analysis:
                results.append(analysis)
        
        return results
    
    def _extract_image_urls(self, html_content: str, base_url: str) -> list[str]:
        """Extract image URLs from HTML content.
        
        Args:
            html_content: The HTML content.
            base_url: Base URL for resolving relative paths.
            
        Returns:
            List of absolute image URLs.
        """
        # Simple regex-based extraction (for TDD - could use BeautifulSoup in production)
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        matches = re.findall(img_pattern, html_content, re.IGNORECASE)
        
        urls = []
        for match in matches:
            # Resolve relative URLs
            absolute_url = urljoin(base_url, match)
            
            # Filter out common non-content images
            if not self._is_ui_icon(absolute_url):
                urls.append(absolute_url)
        
        return urls
    
    def _is_ui_icon(self, url: str) -> bool:
        """Check if URL is likely a UI icon rather than content image.
        
        Args:
            url: The image URL.
            
        Returns:
            True if likely a UI icon.
        """
        lower_url = url.lower()
        
        # Common UI icon patterns
        ui_patterns = [
            "icon", "logo", "avatar", "spinner", "loader",
            "button", "arrow", "check", "close", "menu",
            "favicon", "sprite", ".svg", "pixel.gif"
        ]
        
        return any(pattern in lower_url for pattern in ui_patterns)
    
    async def _analyze_single_image(self, image_url: str) -> VisionAnalysis | None:
        """Analyze a single image.
        
        Args:
            image_url: The URL of the image to analyze.
            
        Returns:
            VisionAnalysis result, or None if analysis failed.
        """
        try:
            # In production, this would call a vision API (e.g., GPT-4V, Claude Vision)
            # For TDD, return a mock analysis
            return VisionAnalysis(
                image_url=image_url,
                description="Image content analysis (mock - integrate with vision API)",
                detected_text="",
                confidence=0.5,
                metadata={
                    "method": "mock",
                    "note": "Integrate with llm_providers vision capability when available"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze image {image_url}: {e}")
            return None
    
    async def analyze_with_llm(
        self,
        image_url: str,
        prompt: str = "Describe this image in detail."
    ) -> VisionAnalysis | None:
        """Analyze image using an LLM with vision capability.
        
        Args:
            image_url: The URL of the image to analyze.
            prompt: The prompt for the vision model.
            
        Returns:
            VisionAnalysis result, or None if analysis failed.
        """
        # This would integrate with llm_providers when vision is available
        # For now, return mock result
        return VisionAnalysis(
            image_url=image_url,
            description=f"Vision analysis for: {prompt}",
            detected_text="",
            confidence=0.5,
            metadata={"method": "mock_llm_vision"}
        )


async def extract_and_analyze_images(
    html_content: str,
    base_url: str,
    max_images: int = 3
) -> list[VisionAnalysis]:
    """Convenience function to extract and analyze images.
    
    Args:
        html_content: The HTML content.
        base_url: Base URL for resolving relative paths.
        max_images: Maximum images to analyze.
        
    Returns:
        List of VisionAnalysis results.
    """
    analyzer = VisionAnalyzer()
    return await analyzer.analyze_images(html_content, base_url, max_images)


# Alias for backward compatibility with fetchers/__init__.py
VisionAnalysisResult = VisionAnalysis
