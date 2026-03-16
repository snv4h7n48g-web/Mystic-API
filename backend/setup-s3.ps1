# S3 Bucket Setup for Palm Images
# Run from backend/ directory

Write-Host "Setting up S3 bucket for palm images..." -ForegroundColor Cyan
Write-Host ""

$BUCKET_NAME = "mystic-palm-images"
$REGION = "us-east-1"

# Create bucket
Write-Host "Creating S3 bucket: $BUCKET_NAME" -ForegroundColor Yellow
aws s3 mb s3://$BUCKET_NAME --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: Bucket created" -ForegroundColor Green
} else {
    Write-Host "WARNING: Bucket may already exist or creation failed" -ForegroundColor Yellow
}

# Configure CORS
Write-Host ""
Write-Host "Configuring CORS..." -ForegroundColor Yellow
aws s3api put-bucket-cors --bucket $BUCKET_NAME --cors-configuration file://s3-cors.json

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: CORS configured" -ForegroundColor Green
} else {
    Write-Host "ERROR: CORS configuration failed" -ForegroundColor Red
    exit 1
}

# Block public access (we use pre-signed URLs)
Write-Host ""
Write-Host "Configuring bucket security..." -ForegroundColor Yellow
$blockConfig = "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
aws s3api put-public-access-block --bucket $BUCKET_NAME --public-access-block-configuration $blockConfig

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: Public access blocked (using pre-signed URLs)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  S3 Setup Complete!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Bucket: $BUCKET_NAME" -ForegroundColor Cyan
Write-Host "Region: $REGION" -ForegroundColor Cyan
Write-Host ""
Write-Host "Add to your .env file:" -ForegroundColor Yellow
Write-Host "  S3_BUCKET_NAME=mystic-palm-images" -ForegroundColor White
Write-Host ""
