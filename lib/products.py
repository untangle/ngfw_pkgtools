"""Product definitions for ngfw_pkgtools."""

from enum import Enum


class Product(str, Enum):
    """Enumeration of supported products."""
    
    MFW = "mfw"
    NGFW = "ngfw"
    WAF = "waf"
    EFW = "efw"
    VELO = "velo"
    
    @classmethod
    def choices(cls):
        """Return a tuple of product values for argparse choices."""
        return tuple(member.value for member in cls)
    
    def __str__(self):
        """Return the string value of the product."""
        return self.value
