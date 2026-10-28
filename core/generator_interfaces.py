"""Abstract base interfaces for password generator services."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.generator_config import PasswordGeneratorConfig


class BasePasswordGenerator(ABC):
    """Abstract interface defining the contract for password generation services."""

    @abstractmethod
    def generate(self, config: PasswordGeneratorConfig | None = None) -> str:
        """Generates a secure password string conforming to the given configuration.

        Args:
            config: Optional configuration settings (defaults to default config).

        Raises:
            InvalidGeneratorConfigError: If configuration is invalid.
            GeneratorError: If compliant password generation fails within attempt limit.

        Returns:
            Generated secure password string.
        """
