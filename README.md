# NOC Canvas

A Network Operation Center (NOC) canvas application for visualizing and managing network infrastructure.

## Features

- **Interactive Canvas**: Drag and drop network devices onto a zoomable, pannable canvas
- **Device Management**: Support for routers, switches, firewalls, and VPN gateways
- **Device Connections**: Visual connections between network devices
- **Plugin System**: Extensible inventory sources (mock implementations for Nautobot and CheckMK)
- **Authentication**: Username/password authentication system
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Live synchronization between frontend and backend

## Technology Stack

### Frontend
- **Vue 3** with Composition API and TypeScript
- **vue-konva** for interactive canvas rendering
- **Pinia** for state management
- **Vue Router** for navigation
- **Tailwind CSS** for styling
- **Vite** for development and building

### Backend
- **FastAPI** with Python
- **PostgreSQL** database (SQLite for local development)
- **SQLAlchemy** ORM
- **JWT** authentication
- **Pydantic** for data validation
- **Celery** for background job processing
- **Redis** for caching and job queue
- **Netmiko** for device SSH connections

## Project Structure

```
./
├── frontend/                 # Vue 3 frontend application
│   ├── src/
│   │   ├── components/       # Reusable Vue components
│   │   ├── views/           # Page-level components
│   │   ├── layouts/         # Layout components
│   │   ├── stores/          # Pinia stores
│   │   ├── services/        # API services
│   │   ├── router/          # Vue Router configuration
│   │   └── styles/          # CSS and styling
│   └── package.json
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── api/             # API route definitions
│   │   ├── core/            # Core configuration and utilities
│   │   ├── models/          # Database models
│   │   └── services/        # Business logic services
│   └── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

**For Local Development:**
- Node.js 18+ and npm
- Python 3.11+
- Redis 6+ (for background jobs)
- PostgreSQL 15+ (or SQLite for simple local dev)
- Git

**For Docker Deployment:**
- Docker 20.10+
- Docker Compose 2.0+

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables (optional):
   ```bash
   # Create .env file or set environment variables
   export INTERNAL_API_URL=http://localhost:8000
   export NOC_REDIS_HOST=localhost
   export NOC_REDIS_PORT=6379
   ```

5. Start the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. Start the Celery worker (in a separate terminal):
   ```bash
   python start_worker.py
   ```

The backend API will be available at `http://localhost:8000`

**Note:** For background jobs (topology discovery, etc.) to work, both the FastAPI server and Celery worker must be running, along with Redis.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

### Docker Deployment

For production or containerized environments:

1. Navigate to the docker directory:
   ```bash
   cd docker
   ```

2. Configure environment variables:
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

3. Start all services:
   ```bash
   docker-compose up -d
   ```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

For detailed Docker documentation, see [docker/README.md](docker/README.md)

### Development Commands

#### Frontend
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

#### Backend
- `uvicorn app.main:app --reload` - Start FastAPI development server
- `python start_worker.py` - Start Celery worker for background jobs
- `python -m pytest` - Run tests (when implemented)

#### Docker
- `docker-compose up -d` - Start all services in background
- `docker-compose logs -f` - View logs
- `docker-compose down` - Stop all services
- `docker-compose ps` - View service status

## Usage

1. **Login/Register**: Create an account or login with existing credentials
2. **Device Inventory**: Use the left panel to browse available device types
3. **Drag & Drop**: Drag device templates from the inventory to the canvas
4. **Device Management**:
   - Click devices to select them
   - Right-click for context menu options
   - Double-click to edit device properties
5. **Connections**:
   - Enable connection mode with the link button
   - Click connection points on devices to create links
6. **Canvas Controls**:
   - Mouse wheel to zoom
   - Drag to pan
   - Grid toggle for alignment
   - Fit to screen to center all devices

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user info

### Devices
- `GET /api/devices/` - List all devices
- `POST /api/devices/` - Create a new device
- `PUT /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Delete device
- `GET /api/devices/connections` - List connections
- `POST /api/devices/connections` - Create connection

## Device Types

The application supports four main device types:

1. **Router** 🔀 - Network routing devices
2. **Switch** 🔁 - Network switching devices
3. **Firewall** 🛡️ - Security filtering devices
4. **VPN Gateway** 🔐 - VPN termination devices

Each device type has customizable properties and visual representation.

## Background Jobs & Topology Discovery

The application uses Celery for asynchronous background job processing:

### Topology Discovery
- **Automatic Discovery**: Discover network topology by SSH connection to devices
- **Device Data Collection**: Interfaces, IP addresses, ARP tables, MAC tables, routing information
- **CDP/LLDP Neighbors**: Automatic neighbor discovery
- **Background Processing**: Non-blocking execution via Celery workers
- **Progress Tracking**: Real-time job progress updates
- **Caching**: Results cached to database for quick access

### Worker Architecture

In **local development**:
- Celery worker calls `http://localhost:8000` to execute device commands
- FastAPI backend connects to devices via SSH/Netmiko
- Worker caches results to database

In **Docker deployment**:
- Celery worker calls `http://noc-backend:8000` (internal Docker network)
- Same workflow, but using container service names
- Configured via `INTERNAL_API_URL` environment variable

### Supported Discovery Features
- ✅ Network interfaces
- ✅ IP addresses
- ✅ ARP entries
- ✅ Static routes
- ✅ OSPF routes
- ✅ BGP routes
- ✅ MAC address tables
- ✅ CDP neighbors

## Plugin System

The application includes a plugin system for inventory sources:

- **Nautobot Integration**: Connector for Nautobot DCIM
- **CheckMK Integration**: Connector for CheckMK monitoring
- **Manual Entry**: Direct device creation interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Future Enhancements

- [ ] Real Nautobot and CheckMK integrations
- [ ] Device status monitoring
- [ ] Network topology auto-discovery
- [ ] Export/import functionality
- [ ] Multi-user collaboration
- [ ] Advanced device properties
- [ ] Network path visualization
- [ ] Alert management
- [ ] Performance metrics dashboard