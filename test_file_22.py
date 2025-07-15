#!/usr/bin/env python3
"""
Test the file 22 with the improved system
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app', 'Services', 'PreviewService'))

from simple_preview_server_no_env import generate_2d_preview
import base64

def test_file_22():
    """Test file 22 with the improved system"""
    
    # File 22 from the attachment
    test_file = "storage/app/models/1/c1bc34d4-df6e-4caa-900e-5a0d70b41c3c.STL"
    
    print("=" * 80)
    print("TESTING FILE 22 WITH IMPROVED SYSTEM")
    print("=" * 80)
    print(f"📁 File: {os.path.basename(test_file)}")
    print(f"📂 Path: {test_file}")
    print(f"📏 Size: {os.path.getsize(test_file):,} bytes")
    print()
    
    # Generate CAD-style technical drawing
    print("🔧 Generating CAD Technical Drawing...")
    preview_b64 = generate_2d_preview(test_file, width=1600, height=1200)
    
    if preview_b64:
        # Save CAD technical drawing
        preview_data = base64.b64decode(preview_b64)
        output_file = "storage/app/public/previews/file_22_cad_technical.png"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'wb') as f:
            f.write(preview_data)
        
        print(f"✅ CAD Technical Drawing Generated Successfully!")
        print(f"   Output: {output_file}")
        print(f"   Size: {len(preview_data):,} bytes")
        print(f"   URL: http://127.0.0.1:8000/storage/previews/file_22_cad_technical.png")
        print()
        
        print("=" * 80)
        print("SOLUTION: INTEGRATE IMPROVED SYSTEM INTO FRONTEND")
        print("=" * 80)
        print("🔍 PROBLEM: Frontend is using old system")
        print("🔧 SOLUTION: Update the server to use the improved STL parsing")
        print("🎯 RESULT: All new uploads will use the improved system")
        print("=" * 80)
        
        return True
    else:
        print("❌ Failed to generate CAD technical drawing")
        return False

if __name__ == "__main__":
    success = test_file_22()
    sys.exit(0 if success else 1)
