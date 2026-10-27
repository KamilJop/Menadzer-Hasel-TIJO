"""Category enumeration for classifying credentials."""

from enum import Enum


class Category(str, Enum):
    """Supported credential categories."""

    SOCIAL_MEDIA = "Social Media"
    FINANCE = "Finance"
    WORK = "Work"
    PERSONAL = "Personal"
    SHOPPING = "Shopping"
    STREAMING = "Streaming & Media"
    GAMING = "Gaming"
    EDUCATION = "Education"
    DEVELOPMENT = "Development"
    OTHER = "Other"
