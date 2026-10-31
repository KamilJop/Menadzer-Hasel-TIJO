"""Asynchronous website favicon and logo fetcher service with image post-processing."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
import logging
from urllib.parse import urlparse

from PyQt6.QtCore import QByteArray, QObject, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

_logger = logging.getLogger(__name__)

_DEFAULT_FAVICON_API_URL: str = "https://www.google.com/s2/favicons?domain={domain}&sz=64"

_CORNER_ALPHA_THRESHOLD: int = 200
_CORNER_RGB_THRESHOLD: int = 225
_FLOOD_FILL_RGB_THRESHOLD: int = 215
_VISIBLE_ALPHA_THRESHOLD: int = 30
_DARK_PIXEL_RGB_THRESHOLD: int = 80
_LIGHTEN_CANDIDATE_RGB_THRESHOLD: int = 90
_DARK_SILHOUETTE_RATIO_THRESHOLD: float = 0.65
_LIGHT_GLYPH_COLOR: tuple[int, int, int] = (244, 244, 245)


class FaviconImageProcessor:
    """Handles pixel post-processing, background transparency, and dark-mode adaptation for icons."""

    @classmethod
    def clean(cls, pixmap: QPixmap) -> QPixmap:
        """Cuts out opaque white backgrounds from favicons and adapts dark glyphs for dark theme.

        Args:
            pixmap: Input QPixmap image to process.

        Returns:
            Processed transparent QPixmap, or original pixmap if null or smaller than 2x2.
        """
        if pixmap.isNull():
            return pixmap

        image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        width, height = image.width(), image.height()
        if width < 2 or height < 2:
            return pixmap

        if cls._has_white_corners(image, width, height):
            cls._apply_flood_fill_transparency(image, width, height)

        if cls._is_dark_silhouette(image, width, height):
            cls._lighten_dark_pixels(image, width, height)

        return QPixmap.fromImage(image)

    @staticmethod
    def _has_white_corners(image: QImage, width: int, height: int) -> bool:
        """Determines whether all four corners of the image have a solid white color.

        Args:
            image: ARGB32 image to inspect.
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            True if all four corner pixels exceed the white alpha and RGB thresholds.
        """
        corners = [
            image.pixelColor(0, 0),
            image.pixelColor(width - 1, 0),
            image.pixelColor(0, height - 1),
            image.pixelColor(width - 1, height - 1),
        ]
        return all(
            corner.alpha() > _CORNER_ALPHA_THRESHOLD
            and corner.red() > _CORNER_RGB_THRESHOLD
            and corner.green() > _CORNER_RGB_THRESHOLD
            and corner.blue() > _CORNER_RGB_THRESHOLD
            for corner in corners
        )

    @staticmethod
    def _apply_flood_fill_transparency(image: QImage, width: int, height: int) -> None:
        """Performs flood-fill transparency starting from the corners inward on near-white pixels.

        Args:
            image: ARGB32 image modified in-place.
            width: Image width in pixels.
            height: Image height in pixels.
        """
        visited: set[tuple[int, int]] = set()
        queue: deque[tuple[int, int]] = deque([
            (0, 0),
            (width - 1, 0),
            (0, height - 1),
            (width - 1, height - 1),
        ])
        for point in queue:
            visited.add(point)

        transparent_color = QColor(0, 0, 0, 0)
        while queue:
            x, y = queue.popleft()
            color = image.pixelColor(x, y)
            if (
                color.red() > _FLOOD_FILL_RGB_THRESHOLD
                and color.green() > _FLOOD_FILL_RGB_THRESHOLD
                and color.blue() > _FLOOD_FILL_RGB_THRESHOLD
            ):
                image.setPixelColor(x, y, transparent_color)
                for neighbor_x, neighbor_y in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if (
                        0 <= neighbor_x < width
                        and 0 <= neighbor_y < height
                        and (neighbor_x, neighbor_y) not in visited
                    ):
                        visited.add((neighbor_x, neighbor_y))
                        queue.append((neighbor_x, neighbor_y))

    @staticmethod
    def _is_dark_silhouette(image: QImage, width: int, height: int) -> bool:
        """Calculates whether visible pixels predominantly constitute a dark silhouette.

        Args:
            image: ARGB32 image to inspect.
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            True if the ratio of dark visible pixels exceeds the silhouette threshold.
        """
        total_visible = 0
        dark_visible = 0
        for y in range(height):
            for x in range(width):
                color = image.pixelColor(x, y)
                if color.alpha() > _VISIBLE_ALPHA_THRESHOLD:
                    total_visible += 1
                    if (
                        color.red() < _DARK_PIXEL_RGB_THRESHOLD
                        and color.green() < _DARK_PIXEL_RGB_THRESHOLD
                        and color.blue() < _DARK_PIXEL_RGB_THRESHOLD
                    ):
                        dark_visible += 1

        return total_visible > 0 and (dark_visible / total_visible) > _DARK_SILHOUETTE_RATIO_THRESHOLD

    @staticmethod
    def _lighten_dark_pixels(image: QImage, width: int, height: int) -> None:
        """Converts dark pixels to a crisp light color preserving their original alpha channel.

        Args:
            image: ARGB32 image modified in-place.
            width: Image width in pixels.
            height: Image height in pixels.
        """
        light_r, light_g, light_b = _LIGHT_GLYPH_COLOR
        for y in range(height):
            for x in range(width):
                color = image.pixelColor(x, y)
                if (
                    color.alpha() > 0
                    and color.red() < _LIGHTEN_CANDIDATE_RGB_THRESHOLD
                    and color.green() < _LIGHTEN_CANDIDATE_RGB_THRESHOLD
                    and color.blue() < _LIGHTEN_CANDIDATE_RGB_THRESHOLD
                ):
                    image.setPixelColor(
                        x,
                        y,
                        QColor(light_r, light_g, light_b, color.alpha()),
                    )


class FaviconService(QObject):
    """Asynchronously fetches and caches website logo favicons via HTTP."""

    favicon_fetched = pyqtSignal(str, QPixmap)

    def __init__(
        self,
        parent: QObject | None = None,
        network_manager: QNetworkAccessManager | None = None,
        api_url_template: str = _DEFAULT_FAVICON_API_URL,
        image_processor: FaviconImageProcessor | None = None,
    ) -> None:
        """Initializes the favicon service with optional dependency injection.

        Args:
            parent: Optional parent QObject for Qt memory management hierarchy.
            network_manager: Optional custom QNetworkAccessManager instance.
            api_url_template: Format string template containing '{domain}' for API endpoint.
            image_processor: Optional image processor strategy for graphic post-processing.
        """
        super().__init__(parent)
        self._network_manager: QNetworkAccessManager = (
            network_manager if network_manager is not None else QNetworkAccessManager(self)
        )
        self._api_url_template: str = api_url_template
        self._image_processor: FaviconImageProcessor = (
            image_processor if image_processor is not None else FaviconImageProcessor()
        )
        self._cache: dict[str, QPixmap] = {}
        self._pending_callbacks: dict[str, list[Callable[[str, QPixmap], None]]] = {}
        self._in_flight_domains: set[str] = set()

    @staticmethod
    def clean_favicon(pixmap: QPixmap) -> QPixmap:
        """Delegates favicon post-processing to FaviconImageProcessor for backward compatibility.

        Args:
            pixmap: Input QPixmap image to process.

        Returns:
            Cleaned and transparency-adjusted QPixmap.
        """
        return FaviconImageProcessor.clean(pixmap)

    @staticmethod
    def extract_domain(url_or_domain: str) -> str:
        """Extracts a normalized hostname or domain from an arbitrary URL or string.

        Args:
            url_or_domain: Raw URL or domain string to parse.

        Returns:
            Normalized lowercase domain string without protocol, port, path, or 'www.' prefix.
        """
        raw = url_or_domain.strip().lower()
        if not raw:
            return ""

        if not raw.startswith(("http://", "https://")):
            raw = f"https://{raw}"

        parsed = urlparse(raw)
        domain = parsed.netloc or parsed.path
        if ":" in domain:
            domain = domain.split(":")[0]
        if domain.startswith("www."):
            domain = domain[4:]
        return domain

    def get_cached(self, url_or_domain: str) -> QPixmap | None:
        """Checks if a favicon for the specified URL or domain is already cached in memory.

        Args:
            url_or_domain: Target URL or domain to query in cache.

        Returns:
            Cached QPixmap if available, or None if not present in memory.
        """
        domain = self.extract_domain(url_or_domain)
        return self._cache.get(domain)

    def fetch_favicon(
        self,
        url_or_domain: str,
        callback: Callable[[str, QPixmap], None] | None = None,
    ) -> QPixmap | None:
        """Fetches website favicon asynchronously, returning cached instance immediately if present.

        Args:
            url_or_domain: Website address or domain to query.
            callback: Optional callback invoked with (domain, QPixmap) once download completes.

        Returns:
            QPixmap instance if already cached, or None if a background fetch was initiated or is pending.
        """
        domain = self.extract_domain(url_or_domain)
        if not domain:
            return None

        if domain in self._cache:
            cached_pixmap = self._cache[domain]
            if callback is not None:
                callback(domain, cached_pixmap)
            return cached_pixmap

        if callback is not None:
            self._pending_callbacks.setdefault(domain, []).append(callback)

        if domain in self._in_flight_domains:
            return None

        self._in_flight_domains.add(domain)
        self._send_favicon_request(domain)
        return None

    def _send_favicon_request(self, domain: str) -> None:
        """Constructs and initiates a network request for the specified domain favicon.

        Args:
            domain: Target domain to fetch favicon for.
        """
        request_url = QUrl(self._api_url_template.format(domain=domain))
        request = QNetworkRequest(request_url)
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )

        reply: QNetworkReply = self._network_manager.get(request)
        reply.finished.connect(lambda r=reply, d=domain: self._on_reply_finished(r, d))

    def _on_reply_finished(self, reply: QNetworkReply, domain: str) -> None:
        """Handles completion of network HTTP reply for favicon image download.

        Respects the Law of Demeter by interacting with immediate collaborators and
        logs any errors encountered during asynchronous callback invocation.

        Args:
            reply: Active QNetworkReply instance to read and clean up.
            domain: Target domain associated with the request.
        """
        reply.deleteLater()
        self._in_flight_domains.discard(domain)

        if reply.error() != QNetworkReply.NetworkError.NoError:
            self._pending_callbacks.pop(domain, None)
            return

        byte_array: QByteArray = reply.readAll()
        raw_bytes: bytes = bytes(byte_array)
        if not raw_bytes:
            self._pending_callbacks.pop(domain, None)
            return

        pixmap = QPixmap()
        if not pixmap.loadFromData(raw_bytes) or pixmap.isNull():
            self._pending_callbacks.pop(domain, None)
            return

        clean_pixmap = self._image_processor.clean(pixmap)
        self._cache[domain] = clean_pixmap
        self.favicon_fetched.emit(domain, clean_pixmap)

        callbacks = self._pending_callbacks.pop(domain, [])
        for callback in callbacks:
            try:
                callback(domain, clean_pixmap)
            except Exception as error:
                _logger.warning("Error invoking favicon callback for domain '%s': %s", domain, error)


__all__ = [
    "FaviconImageProcessor",
    "FaviconService",
]
