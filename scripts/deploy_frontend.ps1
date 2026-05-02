# Deploy frontend to S3 + invalidate CloudFront cache
# Usage: .\scripts\deploy_frontend.ps1

$AWS_PROFILE   = "idp-sbx-trn-lab-01"
$AWS_REGION    = "ap-southeast-1"
$S3_BUCKET     = "ecommerce-frontend-guru-0xetmqk9"
$FRONTEND_DIR  = ".\frontend"
$BUILD_DIR     = "$FRONTEND_DIR\build"
$AWS_CLI       = "$env:USERPROFILE\awscli\Amazon\AWSCLIV2\aws.exe"

# ── 1. Build React app ────────────────────────────────────────────────────────
Write-Host "`n[1/3] Building React app..." -ForegroundColor Cyan

Push-Location $FRONTEND_DIR
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: npm build failed." -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location

Write-Host "Build complete." -ForegroundColor Green

# ── 2. Sync build output to S3 ───────────────────────────────────────────────
Write-Host "`n[2/3] Uploading to S3 bucket: $S3_BUCKET ..." -ForegroundColor Cyan

& $AWS_CLI s3 sync $BUILD_DIR "s3://$S3_BUCKET" `
    --delete `
    --profile $AWS_PROFILE `
    --region $AWS_REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: S3 sync failed. Make sure your SSO session is active:" -ForegroundColor Red
    Write-Host "  aws sso login --profile $AWS_PROFILE" -ForegroundColor Yellow
    exit 1
}

Write-Host "Upload complete." -ForegroundColor Green

# ── 3. Invalidate CloudFront cache ───────────────────────────────────────────
Write-Host "`n[3/3] Invalidating CloudFront cache..." -ForegroundColor Cyan

# Get distribution ID from Terraform state
$TF_STATE = Get-Content ".\infrastructure\terraform.tfstate" | ConvertFrom-Json
$DIST_ID = ($TF_STATE.resources |
    Where-Object { $_.type -eq "aws_cloudfront_distribution" } |
    Select-Object -First 1).instances[0].attributes.id

if ($DIST_ID) {
    & $AWS_CLI cloudfront create-invalidation `
        --distribution-id $DIST_ID `
        --paths "/*" `
        --profile $AWS_PROFILE `
        --region $AWS_REGION | Out-Null

    Write-Host "Cache invalidated for distribution: $DIST_ID" -ForegroundColor Green
} else {
    Write-Host "WARNING: Could not find CloudFront distribution ID. Skipping invalidation." -ForegroundColor Yellow
}

Write-Host "`nFrontend deployed successfully!" -ForegroundColor Green
Write-Host "It may take 1-2 minutes for CloudFront to propagate the new files." -ForegroundColor Gray
