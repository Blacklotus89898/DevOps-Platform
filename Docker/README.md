# 🐋 The Global Docker Mastery Cheat Sheet

## 🛠️ Image Management & Registry

Beyond building, you need to manage versions and registries.

* **`docker build -t <name>:<tag> .`**: Build an image with a specific version tag.
* **`docker build --no-cache .`**: Force a clean rebuild (ignores cached layers).
* **`docker pull/push <repo>/<image>:<tag>`**: Download or upload images to a registry.
* **`docker tag <image_id> <repo>/<name>:<tag>`**: Retag an image for a specific registry.
* **`docker history <image>`**: See the layers and sizes of an image.
* **`docker rmi $(docker images -q)`**: Remove all local images.

---

## 🚀 Container Operations (Advanced)

Handling the lifecycle like a pro.

* **`docker run -it --rm <image>`**: Run a container interactively and **delete it immediately** after exiting (perfect for testing).
* **`docker run -d --restart unless-stopped <image>`**: Ensure a container restarts if the host reboots or the process crashes.
* **`docker pause/unpause <container>`**: Suspend all processes in a container without killing it.
* **`docker wait <container>`**: Block until a container stops and print its exit code.
* **`docker cp <src_path> <container>:<dest_path>`**: Copy files between your host and a running container.

---

## 🔍 Debugging & Performance Monitoring

When "it works on my machine" fails in production.

* **`docker logs -f --tail 100 <container>`**: Follow logs but only show the last 100 lines.
* **`docker diff <container>`**: Inspect changes made to the container's file system since it started.
* **`docker events`**: Get real-time events from the Docker server (e.g., container deaths).
* **`docker exec -u 0 -it <container> sh`**: Enter a container as the **root user** (if the default user is restricted).
* **`docker port <container>`**: List the port mappings for a specific container.

---

## 💾 Volumes & Networking (Infrastructure)

Connecting services securely and persisting data.

* **`docker volume prune`**: Delete all volumes not used by at least one container.
* **`docker network create --driver bridge <name>`**: Create a private network for your app.
* **`docker network connect <network> <container>`**: Attach a running container to a network on the fly.
* **`docker run --network host <image>`**: Run with host networking (no isolation; use for high-perf networking).

---

## 🏗️ Docker Compose (Multi-Service)

Mastering orchestration for local development.

* **`docker-compose up -d --build`**: Rebuild images and start services in one command.
* **`docker-compose up <service_name>`**: Start only one specific service from the YAML.
* **`docker-compose top`**: Display the running processes of all services in the stack.
* **`docker-compose config`**: Validate and view the rendered Compose file (great for debugging environment variables).
* **`docker-compose pull`**: Pull all images defined in the compose file without starting them.

---

## 🧹 System Maintenance (Cleanup)

Preventing Docker from eating your entire hard drive.

| Command | Action |
| --- | --- |
| **`docker system df -v`** | Show detailed disk usage (which image/container is the biggest?). |
| **`docker container prune`** | Remove all stopped containers. |
| **`docker image prune -a`** | Remove ALL unused images, not just dangling ones. |
| **`du -sh /var/lib/docker`** | (Linux) Check total disk space consumed by the Docker engine. |

---

## 🛡️ Production-Grade Dockerfile Template

This version includes **Security Hardening** and **Buildkit** optimizations.

```dockerfile
# syntax=docker/dockerfile:1
# 👆 Enables advanced Buildkit features

# STAGE 1: Build
FROM node:20-slim AS builder
WORKDIR /app

# Cache dependencies separately
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm install

COPY . .
RUN npm run build

# STAGE 2: Production
FROM node:20-alpine AS runner

# Security: Set environment
ENV NODE_ENV=production
WORKDIR /app

# Copy only what is strictly necessary
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/dist ./dist

# Use 'npm ci' for faster, reliable installs in CI/CD
RUN npm ci --only=production

# Security: Run as non-privileged user
RUN addgroup -S nodegroup && adduser -S nodeuser -G nodegroup
USER nodeuser

# Healthcheck: Tell Docker how to test the app's health
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

EXPOSE 3000
CMD ["node", "dist/main.js"]

```

---

## 🛠️ Full-Stack Compose with Profiles

Professional tip: Use **profiles** to toggle services (like monitoring or DB UIs).

```yaml
version: '3.9'

services:
  api:
    build: .
    env_file: .env # Load variables from a file
    depends_on:
      db:
        condition: service_healthy
    networks:
      - backend

  db:
    image: postgres:15-alpine
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      retries: 5
    networks:
      - backend

  # Only starts if you run: docker-compose --profile debug up
  adminer:
    image: adminer
    ports:
      - "8080:8080"
    profiles: ["debug"]
    networks:
      - backend

volumes:
  db_data:

networks:
  backend:
    driver: bridge

```

---

### 💡 Advanced Work Proficiency Tips

1. **The `.dockerignore` Essentials**:
Always ignore `.git`, `node_modules`, `*.log`, and `.env`. This prevents leaking secrets into image layers.
2. **Use `JSON` Form for CMD**:
Always use `CMD ["node", "index.js"]` instead of `CMD node index.js`. The former allows the process to receive OS signals (like `SIGTERM`), which is required for "graceful shutdowns."
3. **Variable Defaults**:
In your Compose file, use `${PORT:-3000}`. This uses 3000 unless a `PORT` variable is found in your `.env`.
4. **Keep it Small**:
If you don't need a full OS, use **Distroless** images from Google. They contain only your app and its dependencies—no shell, no package manager—making them ultra-secure.

