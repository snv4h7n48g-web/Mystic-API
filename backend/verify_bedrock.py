#!/usr/bin/env python3
"""
Verify AWS Bedrock model access and configuration.
Run this to check if the legacy Nova path and optional Claude Opus persona path are accessible.
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

def check_model_access(response):
    """Check if required/desired models are available."""
    print_header("3. Checking Model Availability")

    if not response:
        return False

    models = response.get('modelSummaries', [])
    model_by_id = {model.get('modelId', ''): model for model in models}

    found_any = False
    for label, env_name, fallback in [
        ("Legacy preview", "BEDROCK_PREVIEW_MODEL", "us.amazon.nova-lite-v1:0"),
        ("Legacy full", "BEDROCK_FULL_MODEL", "us.amazon.nova-pro-v1:0"),
        ("Claude Opus", "BEDROCK_MODEL_CLAUDE_OPUS", ""),
    ]:
        target = os.getenv(env_name, fallback).strip()
        if not target:
            print(f"- {label}: not configured")
            continue
        model = model_by_id.get(target)
        if model:
            found_any = True
            print(f"✓ {label} found: {target}")
            print(f"  Status: {model.get('modelLifecycle', {}).get('status', 'unknown')}")
        else:
            print(f"✗ {label} not found: {target}")

    if not found_any:
        print("\n⚠ None of the configured target models were found in available models")
        print("\nCheck:")
        print("  1. Bedrock model access in your account/region")
        print("  2. Exact model IDs in .env")
        print("  3. AWS region alignment with granted access")
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

        persona_enabled = os.getenv('MYSTIC_USE_PERSONA_ORCHESTRATION', 'false').strip().lower() in {'1', 'true', 'yes', 'on'}
        test_model = (
            os.getenv('MYSTIC_LLM_PROFILE_PREVIEW_MODEL')
            or os.getenv('BEDROCK_MODEL_CLAUDE_OPUS')
            or os.getenv('BEDROCK_PREVIEW_MODEL', 'us.amazon.nova-lite-v1:0')
        ).strip()

        print(f"Testing inference with: {test_model}")
        print(f"Persona orchestration enabled: {persona_enabled}")

        response = client.converse(
            modelId=test_model,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": "Say hello in one word."}]
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
    
    # Check configured models
    if not check_model_access(response):
        print("\n⚠ Configured models may not be accessible")
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
