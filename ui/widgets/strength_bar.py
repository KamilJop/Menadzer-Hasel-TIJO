"""Visual password strength indicator bar component."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from core.strength_level import StrengthLevel
from core.validation_result import ValidationResult
from ui.resources.colors import StrengthColors

_SEGMENT_COUNT: int = 5
_SEGMENT_HEIGHT_PX: int = 4
_SEGMENT_CORNER_RADIUS_PX: int = 2


class StrengthBar(QWidget):
    """Visual multi-segment indicator displaying password strength tiers.

    Adheres to the Single Responsibility Principle (SRP) by focusing strictly on presentation.
    Domain evaluation is decoupled and passed in via ValidationResult or StrengthLevel.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initializes the strength bar widget.

        Args:
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self._current_level: StrengthLevel | None = None
        self._current_score: int | None = None
        self._segments: list[QFrame] = []
        self._strength_label: QLabel

        self._setup_ui()
        self.clear()

    @property
    def level(self) -> StrengthLevel | None:
        """Current displayed strength level.

        Returns:
            Active StrengthLevel or None if unassigned or empty.
        """
        return self._current_level

    @property
    def score(self) -> int | None:
        """Current evaluation score if supplied.

        Returns:
            Normalized integer score (0–100) or None.
        """
        return self._current_score

    @property
    def display_text(self) -> str:
        """Current text displayed on the strength status label.

        Returns:
            String title of the strength state.
        """
        return self._strength_label.text()

    def _setup_ui(self) -> None:
        """Constructs layout containing segmented frames and status label."""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 4, 0, 4)
        root_layout.setSpacing(6)

        segments_layout = QHBoxLayout()
        segments_layout.setContentsMargins(0, 0, 0, 0)
        segments_layout.setSpacing(4)

        for _ in range(_SEGMENT_COUNT):
            segment = QFrame(self)
            segment.setFixedHeight(_SEGMENT_HEIGHT_PX)
            self._segments.append(segment)
            segments_layout.addWidget(segment)

        root_layout.addLayout(segments_layout)

        label_row = QHBoxLayout()
        label_row.setContentsMargins(0, 0, 0, 0)

        self._strength_label = QLabel("Strength: —", self)
        label_row.addWidget(self._strength_label)
        label_row.addStretch()

        root_layout.addLayout(label_row)

    def set_result(self, result: ValidationResult | None) -> None:
        """Updates the visual indicator using a domain ValidationResult instance.

        Args:
            result: ValidationResult instance, or None to reset to empty state.
        """
        if result is None:
            self.clear()
            return
        self.set_strength(result.level, result.score)

    def set_strength(
        self,
        level: StrengthLevel | None,
        score: int | None = None,
    ) -> None:
        """Applies a strength tier and optional score to update segments and label.

        Args:
            level: Target StrengthLevel to display, or None to clear.
            score: Optional normalized score percentage between 0 and 100.
        """
        self._current_level = level
        self._current_score = score

        if level is None:
            self.clear()
            return

        active_hex = StrengthColors.get_color(level).name()
        empty_hex = StrengthColors.EMPTY.name()
        rank = level.rank

        for index, segment in enumerate(self._segments):
            color_hex = active_hex if index < rank else empty_hex
            self._apply_segment_style(segment, color_hex)

        title = level.display_name
        self._strength_label.setText(f"Strength: {title}")
        self._strength_label.setStyleSheet(
            f"color: {active_hex}; font-size: 11px; font-weight: 600;"
        )

    def clear(self) -> None:
        """Resets all segments to empty state and neutralizes label styling."""
        self._current_level = None
        self._current_score = None
        empty_hex = StrengthColors.EMPTY.name()
        muted_hex = StrengthColors.TEXT_MUTED.name()

        for segment in self._segments:
            self._apply_segment_style(segment, empty_hex)

        self._strength_label.setText("Strength: —")
        self._strength_label.setStyleSheet(f"color: {muted_hex}; font-size: 11px;")

    def _apply_segment_style(self, segment: QFrame, color_hex: str) -> None:
        """Applies background color and corner radius to an indicator segment frame.

        Args:
            segment: QFrame segment widget to style.
            color_hex: Hexadecimal color string.
        """
        segment.setStyleSheet(
            f"background-color: {color_hex}; border-radius: {_SEGMENT_CORNER_RADIUS_PX}px;"
        )


__all__ = [
    "StrengthBar",
]
