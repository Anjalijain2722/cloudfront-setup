#!/bin/bash

echo "Updating and installing Docker..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "Adding ubuntu user to docker group..."
sudo usermod -aG docker ubuntu

# Ensure Docker service is running and enabled
echo "Ensuring Docker service is running and restarting if needed..."
# First, try to start/enable
sudo systemctl start docker
sudo systemctl enable docker
# Then, forcefully restart to clear any lingering issues from previous failed states
sudo systemctl restart docker

# Wait for Docker to be truly active and healthy
echo "Waiting for Docker service to become active..."
docker_attempts=0
max_docker_attempts=10
while [ $docker_attempts -lt $max_docker_attempts ]; do
    if sudo systemctl is-active --quiet docker; then
        echo "Docker service is active."
        break
    else
        echo "Docker not active yet. Retrying in 5 seconds..."
        sleep 5
        docker_attempts=$((docker_attempts+1))
    fi
done

if ! sudo systemctl is-active --quiet docker; then
    echo "ERROR: Docker service failed to start after multiple attempts. Please investigate manually."
    sudo systemctl status docker --no-pager # Print full status for debugging
    exit 1 # Exit script if Docker isn't running
fi

echo "Navigating to /home/ubuntu and checking files..."
cd /home/ubuntu/ || { echo "ERROR: Failed to navigate to /home/ubuntu/. Exiting."; exit 1; }

# --- DEBUGGING CHECKS (Keep these for now, they are useful) ---
echo "Listing files in /home/ubuntu/:"
ls -l /home/ubuntu/

echo "Checking docker-compose.yml:"
ls -l /home/ubuntu/docker-compose.yml
cat /home/ubuntu/docker-compose.yml

echo "Checking opensearch_dashboards.yml:"
ls -l /home/ubuntu/opensearch_dashboards.yml
cat /home/ubuntu/opensearch_dashboards.yml

echo "Checking Docker Compose version:"
sudo docker compose version

echo "Checking Docker Info:"
sudo docker info
# --- END DEBUGGING CHECKS ---

echo "Starting Docker Compose for OpenSearch and Dashboards..."
# Check if containers are already running before trying to start
if sudo docker ps -a --format '{{.Names}}' | grep -q 'opensearch' && \
   sudo docker ps -a --format '{{.Names}}' | grep -q 'opensearch-dashboards'; then
    echo "OpenSearch and Dashboards containers already exist. Attempting to restart..."
    sudo docker compose down # Stop and remove old containers
    sudo docker compose up -d # Start fresh
else
    echo "OpenSearch and Dashboards containers not found. Starting them for the first time..."
    sudo docker compose up -d
fi

echo "Docker Compose for OpenSearch and Dashboards initiated."
