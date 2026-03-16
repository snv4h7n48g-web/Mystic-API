#!/usr/bin/env python3
"""
Verify AWS Bedrock model access and configuration.
Run this to check if Nova models are accessible.
"""

import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_credentials():
    """Check if AWS credentials are configured."""
    print_header("1. Checking AWS Credentials")
    
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    # Check if explicit credentials in .env
    if access_key and access_key != 'your_access_key_here':
        print(f"✓ Using explicit credentials from .env")
        print(f"✓ AWS_ACCESS_KEY_ID: {access_key[:8]}...")
        print(f"✓ AWS_SECRET_ACCESS_KEY: {secret_key[:8]}...")
        print(f"✓ AWS_REGION: {region}")
        return True
    
    # Fall back to AWS CLI / default credentials
    print("ℹ No explicit credentials in .env")
    print("✓ Will use AWS CLI / default credentials")
    print(f"✓ AWS_REGION: {region}")
    
    # Try to verify default credentials work
    try:
        import boto3
        sts = boto3.client('sts', region_name=region)
        identity = sts.get_caller_identity()
        print(f"✓ AWS Account: {identity['Account']}")
        print(f"✓ AWS User/Role: {identity['Arn'].split('/')[-1]}")
        return True
    except Exception as e:
        print(f"✗ Could not verify AWS credentials: {str(e)}")
        print("\nPlease ensure:")
        print("  1. AWS CLI is configured: aws configure")
        print("  2. OR add credentials to .env file")
        return False

def check_bedrock_service():
    """Check if Bedrock service is accessible."""
    print_header("2. Testing Bedrock Service Access")
    
    try:
        client = boto3.client(
            'bedrock',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Try to list foundation models
        response = client.list_foundation_models()
        
        print(f"✓ Bedrock service accessible")
        print(f"✓ Found {len(response.get('modelSummaries', []))} foundation models")
        
        return True, response
        
    except client.exceptions.AccessDeniedException:
        print("✗ Access denied to Bedrock service")
        print("\nYour IAM user/role needs these permissions:")
        print("  - bedrock:ListFoundationModels")
        print("  - bedrock:InvokeModel")
        print("\nAdd this policy to your IAM user/role:")
        print("""
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:ListFoundationModels",
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
        """)
        return False, None
        
    except Exception as e:
        print(f"✗ Error accessing Bedrock: {str(e)}")
        return False, None

def check_nova_models(response):
    """Check if Nova models are available."""
    print_header("3. Checking Nova Model Availability")
    
    if not response:
        return False
    
    models = response.get('modelSummaries', [])
    
    # Look for Nova models
    nova_lite = None
    nova_pro = None
    
    for model in models:
        model_id = model.get('modelId', '')
        model_name = model.get('modelName', '')
        
        if 'nova-lite' in model_id.lower():
            nova_lite = model
        elif 'nova-pro' in model_id.lower():
            nova_pro = model
    
    if nova_lite:
        print(f"✓ Nova Lite found: {nova_lite['modelId']}")
        print(f"  Status: {nova_lite.get('modelLifecycle', {}).get('status', 'unknown')}")
    else:
        print("✗ Nova Lite not found")
        print("\nNova Lite may not be available in your region or account")
    
    if nova_pro:
        print(f"✓ Nova Pro found: {nova_pro['modelId']}")
        print(f"  Status: {nova_pro.get('modelLifecycle', {}).get('status', 'unknown')}")
    else:
        print("✗ Nova Pro not found")
        print("\nNova Pro may not be available in your region or account")
    
    if not nova_lite and not nova_pro:
        print("\n⚠ Nova models not found in available models")
        print("\nPossible reasons:")
        print("  1. Nova models not available in your region")
        print("  2. Model access not enabled in Bedrock console")
        print("  3. Account doesn't have access to Nova models")
        print("\nTo enable model access:")
        print("  1. Go to: https://console.aws.amazon.com/bedrock/")
        print("  2. Click 'Model access' in left sidebar")
        print("  3. Click 'Manage model access'")
        print("  4. Enable 'Amazon Nova Lite' and 'Amazon Nova Pro'")
        print("  5. Wait for access to be granted (usually immediate)")
        
        return False
    
    return True

def test_inference():
    """Test actual model inference."""
    print_header("4. Testing Model Inference")
    
    try:
        client = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Try a simple inference with Nova Lite
        preview_model = os.getenv('BEDROCK_PREVIEW_MODEL', 'us.amazon.nova-lite-v1:0')
        
        print(f"Testing inference with: {preview_model}")
        
        response = client.converse(
            modelId=preview_model,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": "Say 'hello' in one word."}]
                }
            ],
            inferenceConfig={
                "maxTokens": 10,
                "temperature": 0.7
            }
        )
        
        output = response['output']['message']['content'][0]['text']
        usage = response.get('usage', {})
        
        print(f"✓ Inference successful!")
        print(f"  Response: {output}")
        print(f"  Input tokens: {usage.get('inputTokens', 0)}")
        print(f"  Output tokens: {usage.get('outputTokens', 0)}")
        
        return True
        
    except client.exceptions.AccessDeniedException:
        print("✗ Access denied for model inference")
        print("\nModel access may not be enabled for your account")
        print("Enable model access in Bedrock console (see step 3)")
        return False
        
    except client.exceptions.ValidationException as e:
        print(f"✗ Model validation error: {str(e)}")
        print("\nThe model ID may be incorrect or not available in your region")
        return False
        
    except Exception as e:
        print(f"✗ Inference failed: {str(e)}")
        return False

def main():
    """Run all verification checks."""
    print("\n" + "="*60)
    print("  AWS BEDROCK MODEL ACCESS VERIFICATION")
    print("="*60)
    
    # Check credentials
    if not check_credentials():
        print("\n❌ Please configure AWS credentials in .env file")
        return 1
    
    # Check Bedrock service
    success, response = check_bedrock_service()
    if not success:
        print("\n❌ Cannot access Bedrock service")
        return 1
    
    # Check Nova models
    if not check_nova_models(response):
        print("\n⚠ Nova models may not be accessible")
        print("You can still try running the API, but model calls will fail")
        return 1
    
    # Test inference
    if not test_inference():
        print("\n❌ Model inference test failed")
        return 1
    
    # Success
    print_header("✅ ALL CHECKS PASSED")
    print("Your AWS Bedrock configuration is ready!")
    print("\nYou can now start the API server:")
    print("  ./start.sh")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
