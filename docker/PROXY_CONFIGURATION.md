# Proxy Configuration for NOC Canvas Docker Deployment

This document explains how to configure and deploy NOC Canvas in corporate environments that require proxy settings for internet access.

## Overview

NOC Canvas Docker deployment supports HTTP/HTTPS proxy configuration for:
- Docker image pulling
- Python package installation (pip)
- Node.js package installation (npm)
- Build-time dependency downloads

## Environment Variables

Configure these environment variables in your system or shell profile:

```bash
# Required proxy settings
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8080

# Optional: bypass proxy for local/internal addresses
export NO_PROXY="localhost,127.0.0.1,.company.com,internal.domain"

# Alternative formats also supported
export http_proxy=$HTTP_PROXY
export https_proxy=$HTTPS_PROXY
export no_proxy=$NO_PROXY
```

## Docker Daemon Proxy Configuration

For Docker to pull images through a proxy, configure the Docker daemon:

### Linux (systemd)

1. Create Docker service directory:
```bash
sudo mkdir -p /etc/systemd/system/docker.service.d
```

2. Create proxy configuration file:
```bash
sudo cat > /etc/systemd/system/docker.service.d/http-proxy.conf << EOF
[Service]
Environment="HTTP_PROXY=http://proxy.company.com:8080"
Environment="HTTPS_PROXY=https://proxy.company.com:8080"
Environment="NO_PROXY=localhost,127.0.0.1,.company.com"
EOF
```

3. Restart Docker:
```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### macOS (Docker Desktop)

1. Open Docker Desktop
2. Go to Settings → Resources → Proxies
3. Enable "Manual proxy configuration"
4. Enter your proxy settings

### Windows (Docker Desktop)

1. Open Docker Desktop
2. Go to Settings → Resources → Proxies
3. Enable "Manual proxy configuration"
4. Enter your proxy settings

## Deployment Methods

### Method 1: Air-gapped Deployment (Recommended for Corporate)

Use the prepare-airgapped script which automatically detects and uses proxy settings:

```bash
# Set proxy environment variables first
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8080
export NO_PROXY="localhost,127.0.0.1,.company.com"

# Run air-gapped preparation
cd docker
chmod +x prepare-airgapped.sh
./prepare-airgapped.sh
```

The script will:
- Detect proxy settings automatically
- Configure npm and pip to use proxies during build
- Pull required Docker images through proxy
- Create deployment package for offline installation

### Method 2: Direct Docker Compose

For direct deployment with proxy support:

```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8080
export NO_PROXY="localhost,127.0.0.1,.company.com"

# Test the deployment
cd docker
chmod +x test-docker.sh
./test-docker.sh
```

### Method 3: Manual Docker Build

For manual builds with proxy:

```bash
# Backend
docker build \
  --build-arg HTTP_PROXY=$HTTP_PROXY \
  --build-arg HTTPS_PROXY=$HTTPS_PROXY \
  --build-arg NO_PROXY=$NO_PROXY \
  -f docker/Dockerfile.backend \
  -t noc-backend .

# Worker
docker build \
  --build-arg HTTP_PROXY=$HTTP_PROXY \
  --build-arg HTTPS_PROXY=$HTTPS_PROXY \
  --build-arg NO_PROXY=$NO_PROXY \
  -f docker/Dockerfile.worker \
  -t noc-worker .

# Frontend
docker build \
  --build-arg HTTP_PROXY=$HTTP_PROXY \
  --build-arg HTTPS_PROXY=$HTTPS_PROXY \
  --build-arg NO_PROXY=$NO_PROXY \
  -f docker/Dockerfile.frontend \
  -t noc-frontend .
```

## Troubleshooting

### Common Issues

1. **Docker pull fails**
   - Ensure Docker daemon is configured for proxy
   - Check proxy URL format (http:// or https://)
   - Verify proxy authentication if required

2. **npm install fails during build**
   - Check if corporate firewall blocks npm registry
   - Verify HTTPS_PROXY is correctly set
   - Consider using internal npm registry

3. **pip install fails during build**
   - Verify proxy supports HTTPS for PyPI
   - Check if corporate firewall blocks PyPI
   - Consider using internal PyPI mirror

4. **SSL certificate issues**
   - Add corporate CA certificates to containers
   - Use `--build-arg CERT_PATH=/path/to/cert` if needed

### Debug Commands

Check proxy detection:
```bash
./prepare-airgapped.sh | head -20
```

Test Docker proxy settings:
```bash
docker run --rm alpine/curl:latest curl -I https://pypi.org/simple/
```

Check container proxy settings:
```bash
docker run --rm noc-backend env | grep -i proxy
```

## Security Considerations

1. **Proxy Authentication**: If your proxy requires authentication, include credentials in the URL:
   ```bash
   export HTTP_PROXY=http://username:password@proxy.company.com:8080
   ```

2. **Certificate Validation**: In secure environments, ensure SSL certificates are properly validated

3. **No Proxy Settings**: Carefully configure NO_PROXY to avoid sending internal traffic through proxy

## Advanced Configuration

### Corporate CA Certificates

If your organization uses custom CA certificates:

1. Copy certificates to `docker/certs/` directory
2. Modify Dockerfiles to include:
   ```dockerfile
   COPY docker/certs/*.crt /usr/local/share/ca-certificates/
   RUN update-ca-certificates
   ```

### Internal Package Repositories

Configure for internal repositories:

```bash
# npm
export NPM_REGISTRY=https://npm.internal.company.com
export NPM_CA_FILE=/path/to/ca.pem

# pip
export PIP_INDEX_URL=https://pypi.internal.company.com/simple
export PIP_TRUSTED_HOST=pypi.internal.company.com
```

## Testing Proxy Configuration

Use the test script to verify proxy configuration:

```bash
cd docker
./test-docker.sh
```

The script will show proxy detection status and build logs for troubleshooting.