#!/bin/bash
echo "=== DIAGNOSING n8n RESTART LOOP ==="

# 1. Check system resources
echo -e "\n1. System Resources:"
free -h
echo "---"
df -h .

# 2. Clean everything
echo -e "\n2. Cleaning up..."
sudo docker compose down 2>/dev/null
sudo docker system prune -a -f 2>/dev/null

# 3. Remove old data
echo -e "\n3. Removing old data..."
sudo rm -rf postgres_data n8n_data redis_data 2>/dev/null
mkdir -p postgres_data n8n_data redis_data
sudo chmod 777 -R postgres_data n8n_data redis_data

# 4. Create MINIMAL .env
echo -e "\n4. Creating minimal .env..."
cat > .env << 'ENVEOF'
POSTGRES_USER=n8n
POSTGRES_PASSWORD=n8n123
POSTGRES_DB=n8n
N8N_ENCRYPTION_KEY=testkey1234567890
GENERIC_TIMEZONE=UTC
ENVEOF

# 5. Create MINIMAL docker-compose.yml
echo -e "\n5. Creating minimal docker-compose.yml..."
cat > docker-compose.yml << 'YAMLEOF'
services:
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: \${POSTGRES_USER}
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
      POSTGRES_DB: \${POSTGRES_DB}
    volumes:
      - ./postgres_data:/var/lib/postgresql/data

  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - DB_TYPE=sqlite
      - DB_SQLITE_DATABASE=/home/node/.n8n/database.sqlite
      - N8N_ENCRYPTION_KEY=\${N8N_ENCRYPTION_KEY}
      - N8N_PROTOCOL=http
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
    volumes:
      - ./n8n_data:/home/node/.n8n
YAMLEOF

# 6. Start just n8n with SQLite (no PostgreSQL dependency)
echo -e "\n6. Starting n8n with SQLite..."
sudo docker compose up -d n8n

# 7. Wait and check status
echo -e "\n7. Waiting 20 seconds..."
sleep 20

echo -e "\n8. Checking status:"
sudo docker compose ps

echo -e "\n9. Checking logs (last 30 lines):"
sudo docker compose logs n8n --tail=30

echo -e "\n10. Checking for errors:"
sudo docker compose logs n8n 2>&1 | tail -50 | grep -i "error\|fail\|exception\|crash\|timeout"
