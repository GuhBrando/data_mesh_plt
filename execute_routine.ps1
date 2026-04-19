# Shell script to load environment variables and execute the SQL script inside the Docker container

# Step 1: Load environment variables from .env
Get-Content .env | ForEach-Object {
    if ($_ -match "^(.*?)=(.*)$") {
        Set-Item -Path "Env:$($matches[1])" -Value "$($matches[2])"
    }
}

# Step 2: Execute the SQL script inside the Docker container
$containerName = "postgres_db"  # Replace with your container name
$scriptPath = "/roles_and_permissions.sql"  # Path inside the container

# Run the psql command inside the container
docker exec -i $containerName sh -c "psql -U admin -d data_mesh_plt -f $scriptPath"

# Step 3: Check for errors
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to execute the SQL script inside the Docker container." -ForegroundColor Red
    exit $LASTEXITCODE
} else {
    Write-Host "Success: SQL script executed successfully inside the Docker container." -ForegroundColor Green
}