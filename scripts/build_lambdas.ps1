# Services to package — 5 Lambda functions + order processor
$services = @("catalog_service", "user_service", "order_service", "payment_service", "order_processor", "admin_service")

Write-Host "Packaging Lambda functions..."

foreach ($service in $services) {
    $zipName = ".\${service}_guru.zip"

    # Remove old zip if it exists
    if (Test-Path $zipName) {
        Remove-Item $zipName
    }

    Write-Host "Zipping $service..."

    # Compress the service file
    Compress-Archive -Path ".\services\${service}.py" -DestinationPath $zipName -Update

    # Always bundle shared utils
    if (Test-Path ".\services\utils.py") {
        Compress-Archive -Path ".\services\utils.py" -DestinationPath $zipName -Update
    }
}

Write-Host "Done! All Lambda packages built successfully."
