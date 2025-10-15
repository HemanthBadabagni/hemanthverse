#!/usr/bin/env python3
"""
Visual Test Page - Compare different background image settings
"""

import streamlit as st
import base64
from PIL import Image
from io import BytesIO

def get_image_base64():
    """Get the local image as base64"""
    try:
        if os.path.exists("IMG_7653.PNG"):
            with open("IMG_7653.PNG", 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        st.error(f"Error loading image: {e}")
    return None

def display_test_card(title, background_style, image_bytes):
    """Display a test invitation card with specific background style"""
    st.markdown(f"### {title}")
    
    if image_bytes:
        st.markdown(
            f"""
            <div style="position:relative;{background_style}padding:2em;border-radius:16px;border:2px solid #d4af37;font-family:'Noto Serif',serif;box-shadow:2px 2px 20px #a80000;overflow:hidden;margin:1em 0;">
                <div style="text-align:center;position:relative;z-index:1;">
                    <div style='font-size:1.2em;color:#000000;font-weight:bold;margin-bottom:1em;text-shadow:2px 2px 4px rgba(255,255,255,0.8);'>ॐ श्री गणेशाय नमः</div>
                    <span style="font-size:2.2em;color:#000000;font-weight:bold;text-shadow:2px 2px 4px rgba(255,255,255,0.8);">Shubha Gruha Praveshah</span><br>
                    <span style="font-size:1.2em;color:#000000;font-weight:600;text-shadow:1px 1px 2px rgba(255,255,255,0.8);">Hosted by Mounika, Hemanth & Viraj</span><br>
                    <span style="font-size:1em;color:#000000;font-weight:500;text-shadow:1px 1px 2px rgba(255,255,255,0.8);">13-Nov-2025 at 04:00 PM</span><br>
                    <span style="font-size:0.9em;color:#000000;font-weight:500;text-shadow:1px 1px 2px rgba(255,255,255,0.8);">Venue: 3108 Honerywood Drive, Leander, TX -78641</span>
                </div>
                <hr style="border:2px solid #000000;margin:1em 0;position:relative;z-index:1;">
                <div style="font-size:1em;color:#000000;margin:1em 0;position:relative;z-index:1;font-weight:500;text-shadow:1px 1px 2px rgba(255,255,255,0.8);line-height:1.4;">
                    An Abode of Happiness and Blessings
                </div>
            </div>
            """, unsafe_allow_html=True
        )

def main():
    st.title("🎨 Image Display Test - Compare Different Settings")
    
    # Load the image
    image_bytes = get_image_base64()
    
    if not image_bytes:
        st.error("❌ Could not load IMG_7653.PNG")
        return
    
    st.success("✅ Image loaded successfully (1024x1536 pixels)")
    
    # Test different background styles
    st.markdown("## 📊 Compare Different Background Settings")
    
    # Original (cover) - crops image
    display_test_card(
        "❌ OLD: background-size: cover (CROPS IMAGE)",
        f"background: url('data:image/png;base64,{image_bytes}') center center / cover no-repeat;background-color: #f6eedf;min-height: 600px;position: relative;",
        image_bytes
    )
    
    # Fixed (contain) - shows full image
    display_test_card(
        "✅ NEW: background-size: contain (SHOWS FULL IMAGE)",
        f"background: url('data:image/png;base64,{image_bytes}') center center / contain no-repeat;background-color: #f6eedf;min-height: 800px;position: relative;",
        image_bytes
    )
    
    # Stretched - fills container
    display_test_card(
        "🔧 ALTERNATIVE: background-size: 100% 100% (STRETCHES IMAGE)",
        f"background: url('data:image/png;base64,{image_bytes}') center center / 100% 100% no-repeat;background-color: #f6eedf;min-height: 600px;position: relative;",
        image_bytes
    )
    
    st.markdown("---")
    st.markdown("### 🎯 What to Look For:")
    st.markdown("""
    - **❌ OLD (cover)**: Parts of the image will be cropped/cut off
    - **✅ NEW (contain)**: Full image visible, no cropping
    - **🔧 ALTERNATIVE (100% 100%)**: Image stretched to fill container
    
    **The NEW setting should show your complete family image without any parts being cut off!**
    """)
    
    st.markdown("### 🌐 Test the Real App:")
    st.markdown("Go to: **http://localhost:8501** and click 'Create Test Invitation'")

if __name__ == "__main__":
    main()

