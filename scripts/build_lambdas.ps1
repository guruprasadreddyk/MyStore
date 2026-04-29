$services = @("product_service", "cart_service", "order_service", "payment_service", "search_service", "order_processor", "wishlist_service")

Write-Host "Packaging Lambda functions..."

foreach ($service in $services) {
    $zipName = ".\${service}_guru.zip"
    
    # Remove old zip if it exists
    if (Test-Path $zipName) {
        Remove-Item $zipName
    }
    
    Write-Host "Zipping $service..."
    
    # Compress the specific service file
    Compress-Archive -Path ".\services\${service}.py" -DestinationPath $zipName -Update
    
    # If the service imports utils (or just to be safe, include it in all), append it
    if (Test-Path ".\services\utils.py") {
        Compress-Archive -Path ".\services\utils.py" -DestinationPath $zipName -Update
    }
}

Write-Host "Done! All services packaged successfully."
