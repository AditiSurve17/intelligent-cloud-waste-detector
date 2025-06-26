# File: tests/lambda-test.py
# Python script to test Lambda functions locally
# Run: python tests/lambda-test.py

import json
import sys
import os

# Add the lambda functions directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda-functions'))

def test_data_collector():
    """Test the data collector Lambda function"""
    print("🧪 Testing cwd-data-collector function...")
    
    try:
        # Import the Lambda function
        import cwd_data_collector as collector
        
        # Test event
        test_event = {
            "test_direct": True
        }
        
        # Mock context
        class MockContext:
            def __init__(self):
                self.function_name = "cwd-data-collector"
                self.memory_limit_in_mb = 256
                self.invoked_function_arn = "arn:aws:lambda:ap-south-1:123456789012:function:cwd-data-collector"
        
        context = MockContext()
        
        # Call the function
        result = collector.lambda_handler(test_event, context)
        
        print(f"✅ Data collector test passed")
        print(f"Response: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"❌ Data collector test failed: {str(e)}")

def test_advanced_analytics():
    """Test the advanced analytics Lambda function"""
    print("\n🧪 Testing cwd-advanced-analytics function...")
    
    try:
        # Import the Lambda function
        import cwd_advanced_analytics as analytics
        
        # Test event
        test_event = {
            "analytics_type": "weekly_summary",
            "force_refresh": True
        }
        
        # Mock context
        class MockContext:
            def __init__(self):
                self.function_name = "cwd-advanced-analytics"
                self.memory_limit_in_mb = 256
                self.invoked_function_arn = "arn:aws:lambda:ap-south-1:123456789012:function:cwd-advanced-analytics"
        
        context = MockContext()
        
        # Call the function
        result = analytics.lambda_handler(test_event, context)
        
        print(f"✅ Advanced analytics test passed")
        print(f"Response: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"❌ Advanced analytics test failed: {str(e)}")

def main():
    """Run all tests"""
    print("🚀 Starting Lambda function tests...")
    print("Note: These are syntax/import tests. Full functionality requires AWS resources.")
    print("=" * 60)
    
    test_data_collector()
    test_advanced_analytics()
    
    print("\n" + "=" * 60)
    print("✨ Testing completed!")
    print("\nFor full testing:")
    print("1. Deploy functions to AWS using scripts/deploy.sh")
    print("2. Test in AWS Lambda console with test events")
    print("3. Check CloudWatch logs for detailed execution results")

if __name__ == "__main__":
    main()