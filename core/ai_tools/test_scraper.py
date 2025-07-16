#!/usr/bin/env python3
"""
Simple test script for the Gateway EOB Scraper.
This script can be run directly to test the basic functionality.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gateway_eob_scraper import GatewayEOBScraper
    print("✅ Successfully imported GatewayEOBScraper")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_basic_functionality():
    """Test basic scraper functionality without requiring a PDF file."""
    print("\n🧪 Testing basic scraper functionality...")
    
    try:
        # Initialize the scraper
        scraper = GatewayEOBScraper()
        print("✅ Scraper initialized successfully")
        
        # Test model connection
        print("🔗 Testing model connection...")
        if scraper.ollama_client.test_model_connection():
            print("✅ Model connection successful")
        else:
            print("⚠️ Model connection failed - this is okay for testing")
        
        # Test with a dummy PDF path
        print("📄 Testing PDF processing (with non-existent file)...")
        try:
            result = scraper.process_pdf("non_existent_file.pdf")
        except FileNotFoundError:
            print("✅ Correctly handled non-existent file")
        except Exception as e:
            print(f"⚠️ Unexpected error: {e}")
        
        print("\n🎉 Basic functionality test completed!")
        print("📝 To test with a real PDF, update the pdf_file path in example_usage.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_with_sample_data():
    """Test analysis functionality with sample data."""
    print("\n🧪 Testing analysis functionality with sample data...")
    
    try:
        scraper = GatewayEOBScraper()
        
        # Create sample claims data
        sample_claims = [
            "Claim Information\nPatient: John Doe\nService: Office Visit\nBilled: $150\nAllowed: $120\nPatient Responsibility: $30",
            "Claim Information\nPatient: John Doe\nService: Lab Test\nBilled: $200\nAllowed: $180\nPatient Responsibility: $20"
        ]
        
        # Set the claims data directly
        scraper.claims = sample_claims
        scraper.extracted_data = "\n\n".join(sample_claims)
        
        print("✅ Sample data loaded")
        
        # Test summary analysis
        print("📊 Testing summary analysis...")
        summary = scraper.analyze_claims_with_ai("summary")
        if summary:
            print("✅ Summary analysis successful")
            print(f"📋 Summary preview: {summary[:100]}...")
        else:
            print("⚠️ Summary analysis failed - this might be due to model connection")
        
        print("\n🎉 Analysis functionality test completed!")
        
    except Exception as e:
        print(f"❌ Analysis test failed: {e}")

if __name__ == "__main__":
    print("🚀 Gateway EOB Scraper Test Suite")
    print("=" * 40)
    
    test_basic_functionality()
    test_with_sample_data()
    
    print("\n📚 Next Steps:")
    print("1. Place your EOB PDF file in this directory")
    print("2. Update the pdf_file path in example_usage.py")
    print("3. Run: python example_usage.py")
    print("4. Or run: python gateway_eob_scraper.py") 