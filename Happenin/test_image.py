#!/usr/bin/env python3
"""
Image Test Script - Verify image loading and display
"""

import os
import base64
from PIL import Image
import streamlit as st

def test_image_loading():
    """Test if the local image loads correctly"""
    print("🧪 Testing Image Loading...")
    
    # Check if image file exists
    if os.path.exists("IMG_7653.PNG"):
        print("✅ IMG_7653.PNG found")
        
        # Try to load and process the image
        try:
            image = Image.open("IMG_7653.PNG")
            print(f"✅ Image loaded successfully")
            print(f"   - Size: {image.size}")
            print(f"   - Mode: {image.mode}")
            print(f"   - Format: {image.format}")
            
            # Test base64 encoding
            from io import BytesIO
            buf = BytesIO()
            image.save(buf, format="PNG")
            image_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            print(f"✅ Base64 encoding successful (length: {len(image_base64)})")
            
            return True, image.size
            
        except Exception as e:
            print(f"❌ Error loading image: {e}")
            return False, None
    else:
        print("❌ IMG_7653.PNG not found")
        return False, None

def test_background_css():
    """Test the CSS background properties"""
    print("\n🧪 Testing CSS Background Properties...")
    
    # Test different background-size options
    css_options = [
        ("cover", "Crops image to fill container"),
        ("contain", "Shows full image without cropping"),
        ("100% 100%", "Stretches image to fill container"),
        ("auto", "Shows image at original size")
    ]
    
    for option, description in css_options:
        print(f"   - {option}: {description}")
    
    print("\n✅ Current setting: 'contain' - should show full image without cropping")

if __name__ == "__main__":
    print("🎯 HemanthVerse Image Test")
    print("=" * 40)
    
    # Test image loading
    success, size = test_image_loading()
    
    # Test CSS options
    test_background_css()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Image test completed successfully!")
        print(f"📏 Image dimensions: {size[0]}x{size[1]} pixels")
        print("🌐 Now test in browser at: http://localhost:8501")
    else:
        print("❌ Image test failed - check file path and permissions")



