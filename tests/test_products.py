"""Unit tests for Product enum."""

import unittest
from lib.products import Product


class TestProduct(unittest.TestCase):
    """Test cases for Product enum."""
    
    def test_product_values(self):
        """Test that all expected products are defined."""
        self.assertEqual(Product.MFW.value, "mfw")
        self.assertEqual(Product.NGFW.value, "ngfw")
        self.assertEqual(Product.WAF.value, "waf")
        self.assertEqual(Product.EFW.value, "efw")
        self.assertEqual(Product.VELO.value, "velo")
    
    def test_product_choices(self):
        """Test that choices() returns all product values."""
        choices = Product.choices()
        
        self.assertIsInstance(choices, tuple)
        self.assertEqual(len(choices), 5)
        self.assertIn("mfw", choices)
        self.assertIn("ngfw", choices)
        self.assertIn("waf", choices)
        self.assertIn("efw", choices)
        self.assertIn("velo", choices)
    
    def test_product_str(self):
        """Test that Product enum converts to string correctly."""
        self.assertEqual(str(Product.MFW), "mfw")
        self.assertEqual(str(Product.NGFW), "ngfw")
    
    def test_product_is_string_enum(self):
        """Test that Product members are string instances."""
        self.assertIsInstance(Product.MFW, str)
        self.assertIsInstance(Product.NGFW, str)
    
    def test_product_comparison(self):
        """Test that Product enum can be compared with strings."""
        self.assertEqual(Product.MFW, "mfw")
        self.assertEqual(Product.NGFW, "ngfw")
        self.assertNotEqual(Product.MFW, "ngfw")


if __name__ == '__main__':
    unittest.main()
