#!/bin/bash
sudo apt update -y
sudo apt install -y docker.io unzip
sudo systemctl enable docker
sudo systemctl start docker

docker-compose -f /home/ubuntu/docker-compose.yml up -d