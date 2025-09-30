"""
Test script for PDF extraction API
Run locally or against deployed Modal endpoint
"""

import requests
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your Modal URL after deployment
# BASE_URL = "https://your-username--pdf-extraction-playground-fastapi-app.modal.run"

def test_health():
    """Test health check endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print("-" * 50)

def test_models():
    """Test models listing endpoint"""
    print("Testing models endpoint...")
    response = requests.get(f"{BASE_URL}/models")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print("-" * 50)

def test_upload(pdf_path: str):
    """Test PDF upload endpoint"""
    print(f"Testing upload with {pdf_path}...")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
        data = {'model': 'docling'}
        
        response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    print("-" * 50)

def test_extraction(pdf_path: str):
    """Test PDF extraction endpoint"""
    print(f"Testing extraction with {pdf_path}...")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
        data = {'model': 'docling'}
        
        response = requests.post(f"{BASE_URL}/extract", files=files, data=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nExtraction successful!")
            print(f"Model: {result.get('model')}")
            print(f"Processing time: {result.get('processing_time_ms')} ms")
            print(f"\nStatistics:")
            print(json.dumps(result.get('statistics', {}), indent=2))
            
            print(f"\nExtracted {len(result.get('elements', []))} elements")
            
            # Show first few elements
            elements = result.get('elements', [])
            if elements:
                print(f"\nFirst 3 elements:")
                for elem in elements[:3]:
                    print(f"  - Type: {elem['type']}, Content: {elem['content'][:50]}...")
            
            # Save markdown
            markdown = result.get('markdown', '')
            if markdown:
                output_file = Path(pdf_path).stem + "_extracted.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                print(f"\nMarkdown saved to: {output_file}")
            
            # Save full result
            result_file = Path(pdf_path).stem + "_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f"Full result saved to: {result_file}")
        else:
            print(f"Error: {response.text}")
    
    print("-" * 50)

def main():
    """Run all tests"""
    print("=" * 50)
    print("PDF Extraction API Tests")
    print("=" * 50)
    
    # Test basic endpoints
    test_health()
    test_models()
    
    # Test with a PDF file
    pdf_path = input("\nEnter path to a PDF file to test extraction (or press Enter to skip): ").strip()
    
    if pdf_path and Path(pdf_path).exists():
        test_upload(pdf_path)
        test_extraction(pdf_path)
    else:
        print("No PDF provided or file not found. Skipping extraction tests.")
    
    print("\n" + "=" * 50)
    print("Tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()