#!/bin/bash

################################################################################
# S3 & CloudFront Setup Script
# Menu Knowledge Engine - Image Storage & CDN
#
# Infrastructure:
# - S3 Bucket: menu-knowledge-images
# - CloudFront Distribution: 24h caching
# - Cost Target: < $10/month
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BUCKET_NAME="menu-knowledge-images"
REGION="ap-northeast-2"  # Seoul
AWS_PROFILE="default"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}S3 & CloudFront Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Function: Print step
print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

# Function: Print warning
print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Function: Print error
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check AWS CLI installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Install it first: pip install awscli"
    exit 1
fi

# Step 1: Create S3 bucket
print_step "1/7 - Creating S3 bucket: ${BUCKET_NAME}"

aws s3 mb s3://${BUCKET_NAME} --region ${REGION} --profile ${AWS_PROFILE} 2>&1 || {
    print_warning "Bucket may already exist, continuing..."
}

print_step "✅ S3 bucket ready"

# Step 2: Configure bucket for public read
print_step "2/7 - Configuring public read access"

# Disable block public access
aws s3api put-public-access-block \
    --bucket ${BUCKET_NAME} \
    --public-access-block-configuration \
        "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" \
    --profile ${AWS_PROFILE}

# Create bucket policy
cat > /tmp/bucket-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::menu-knowledge-images/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy \
    --bucket ${BUCKET_NAME} \
    --policy file:///tmp/bucket-policy.json \
    --profile ${AWS_PROFILE}

rm /tmp/bucket-policy.json

print_step "✅ Public read access configured"

# Step 3: Enable versioning (for backup)
print_step "3/7 - Enabling versioning"

aws s3api put-bucket-versioning \
    --bucket ${BUCKET_NAME} \
    --versioning-configuration Status=Enabled \
    --profile ${AWS_PROFILE}

print_step "✅ Versioning enabled"

# Step 4: Configure lifecycle policy (cost optimization)
print_step "4/7 - Configuring lifecycle policy"

cat > /tmp/lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "Id": "DeleteOldVersions",
      "Status": "Enabled",
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 30
      }
    },
    {
      "Id": "TransitionToIA",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "STANDARD_IA"
        }
      ],
      "Filter": {
        "Prefix": ""
      }
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
    --bucket ${BUCKET_NAME} \
    --lifecycle-configuration file:///tmp/lifecycle.json \
    --profile ${AWS_PROFILE}

rm /tmp/lifecycle.json

print_step "✅ Lifecycle policy configured"

# Step 5: Create CloudFront distribution
print_step "5/7 - Creating CloudFront distribution"

# Generate CloudFront config
cat > /tmp/cloudfront-config.json << EOF
{
  "CallerReference": "$(date +%s)",
  "Comment": "Menu Knowledge Engine - Image CDN",
  "Enabled": true,
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-${BUCKET_NAME}",
        "DomainName": "${BUCKET_NAME}.s3.${REGION}.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-${BUCKET_NAME}",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000,
    "Compress": true
  },
  "PriceClass": "PriceClass_200",
  "ViewerCertificate": {
    "CloudFrontDefaultCertificate": true
  }
}
EOF

# Create distribution
DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config file:///tmp/cloudfront-config.json \
    --profile ${AWS_PROFILE} \
    --query 'Distribution.Id' \
    --output text)

rm /tmp/cloudfront-config.json

print_step "✅ CloudFront distribution created: ${DISTRIBUTION_ID}"

# Step 6: Wait for distribution to deploy
print_step "6/7 - Waiting for CloudFront deployment (this may take 10-15 minutes)"

aws cloudfront wait distribution-deployed \
    --id ${DISTRIBUTION_ID} \
    --profile ${AWS_PROFILE}

print_step "✅ CloudFront deployed"

# Get CloudFront domain
CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
    --id ${DISTRIBUTION_ID} \
    --profile ${AWS_PROFILE} \
    --query 'Distribution.DomainName' \
    --output text)

# Step 7: Upload test image
print_step "7/7 - Uploading test image"

# Create test image (1x1 transparent PNG)
echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > /tmp/test.png

aws s3 cp /tmp/test.png s3://${BUCKET_NAME}/test.png \
    --acl public-read \
    --profile ${AWS_PROFILE}

rm /tmp/test.png

print_step "✅ Test image uploaded"

# Final summary
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ S3 & CloudFront Setup Complete${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "S3 Bucket: ${BUCKET_NAME}"
echo "Region: ${REGION}"
echo "CloudFront Distribution ID: ${DISTRIBUTION_ID}"
echo "CloudFront Domain: ${CLOUDFRONT_DOMAIN}"
echo ""
echo "Test URLs:"
echo "  S3: https://${BUCKET_NAME}.s3.${REGION}.amazonaws.com/test.png"
echo "  CloudFront: https://${CLOUDFRONT_DOMAIN}/test.png"
echo ""
echo "Next Steps:"
echo "1. Test image access: curl https://${CLOUDFRONT_DOMAIN}/test.png"
echo "2. Update .env file:"
echo "   IMAGE_CDN_URL=https://${CLOUDFRONT_DOMAIN}"
echo "   S3_BUCKET_NAME=${BUCKET_NAME}"
echo "3. Integrate image upload in backend API"
echo ""
echo -e "${YELLOW}Cost Monitoring:${NC}"
echo "aws cloudwatch get-metric-statistics \\"
echo "  --namespace AWS/S3 \\"
echo "  --metric-name BucketSizeBytes \\"
echo "  --dimensions Name=BucketName,Value=${BUCKET_NAME} Name=StorageType,Value=StandardStorage \\"
echo "  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \\"
echo "  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \\"
echo "  --period 86400 \\"
echo "  --statistics Average"
echo ""
