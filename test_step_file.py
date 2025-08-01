#!/usr/bin/env python3
"""
Test script for STEP file analysis and preview generation
Usage: python test_step_file.py <step_file_path>
"""

import sys
import os
import json
import requests
import time

def test_step_analysis(file_path):
    """Test STEP file analysis"""
    print(f"🔍 Testing STEP analysis for: {file_path}")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Test the analyzer directly
    import subprocess
    
    try:
        print("📊 Running STEP analyzer...")
        result = subprocess.run([
            sys.executable, 
            "app/Services/FileAnalyzers/analyze_step_simple.py", 
            file_path
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Analysis successful!")
            
            # Parse the JSON output
            try:
                analysis_data = json.loads(result.stdout)
                print("\n📋 Analysis Results:")
                print(f"   📏 Dimensions: {analysis_data.get('dimensions', 'N/A')}")
                print(f"   ⏱️  Analysis Time: {analysis_data.get('analysis_time_ms', 'N/A')} ms")
                
                metadata = analysis_data.get('metadata', {})
                print(f"   📄 File Name: {metadata.get('file_name', 'N/A')}")
                print(f"   🔧 Schema: {metadata.get('schema', 'N/A')}")
                print(f"   📐 Faces: {metadata.get('faces', 'N/A')}")
                print(f"   📏 Edges: {metadata.get('edges', 'N/A')}")
                print(f"   🔘 Vertices: {metadata.get('vertices', 'N/A')}")
                print(f"   📦 Solids: {metadata.get('solids', 'N/A')}")
                print(f"   💾 File Size: {metadata.get('file_size_kb', 'N/A')} KB")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse analysis output: {e}")
                print(f"Raw output: {result.stdout}")
                return False
                
        else:
            print(f"❌ Analysis failed with return code: {result.returncode}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Analysis timed out")
        return False
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return False

def test_step_preview(file_path, preview_type="2d"):
    """Test STEP preview generation"""
    print(f"\n🖼️  Testing STEP preview generation ({preview_type})...")
    print("=" * 60)
    
    # Check if preview server is running
    try:
        response = requests.get("http://127.0.0.1:8052/health", timeout=5)
        if response.status_code != 200:
            print("❌ Preview server not responding")
            return False
        print("✅ Preview server is running")
    except requests.RequestException:
        print("❌ Preview server not accessible")
        return False
    
    # Generate preview
    try:
        print(f"🎨 Generating {preview_type} preview...")
        
        payload = {
            "file_id": f"test_step_{int(time.time())}",
            "file_path": os.path.abspath(file_path),
            "file_type": "step",
            "preview_type": preview_type,
            "width": 800,
            "height": 600
        }
        
        response = requests.post(
            "http://127.0.0.1:8052/generate_preview",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Preview generation successful!")
            print(f"   📁 Preview file: {result.get('preview_filename', 'N/A')}")
            print(f"   📍 Preview path: {result.get('preview_path', 'N/A')}")
            return True
        else:
            print(f"❌ Preview generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Preview request error: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_step_file.py <step_file_path>")
        print("\nExample:")
        print("  python test_step_file.py tests/test.step")
        print("  python test_step_file.py path/to/your/efector.step")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("🚀 STEP FILE TESTING SUITE")
    print("=" * 60)
    print(f"File: {file_path}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test analysis
    analysis_ok = test_step_analysis(file_path)
    
    if analysis_ok:
        # Test previews
        preview_2d_ok = test_step_preview(file_path, "2d")
        preview_wireframe_ok = test_step_preview(file_path, "wireframe")
        
        print("\n📊 SUMMARY")
        print("=" * 60)
        print(f"✅ Analysis: {'PASS' if analysis_ok else 'FAIL'}")
        print(f"🖼️  2D Preview: {'PASS' if preview_2d_ok else 'FAIL'}")
        print(f"🔲 Wireframe Preview: {'PASS' if preview_wireframe_ok else 'FAIL'}")
        
        if analysis_ok and preview_2d_ok and preview_wireframe_ok:
            print("\n🎉 ALL TESTS PASSED! Your STEP file is fully supported.")
        elif analysis_ok:
            print("\n⚠️  Analysis works but preview generation has issues.")
        else:
            print("\n❌ Analysis failed. Check the file format.")
    
    print("\n💡 Next steps:")
    print("   1. If tests pass, try uploading via web interface")
    print("   2. Check Laravel logs if upload fails")
    print("   3. Verify preview images are generated in public/storage/previews/")

if __name__ == "__main__":
    main()
