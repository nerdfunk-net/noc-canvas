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
- **SQLite** database
- **SQLAlchemy** ORM
- **JWT** authentication
- **Pydantic** for data validation

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

- Node.js 18+ and npm
- Python 3.8+
- Git

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

4. Start the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The backend API will be available at `http://localhost:8000`

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

### Development Commands

#### Frontend
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

#### Backend
- `uvicorn app.main:app --reload` - Start development server
- `python -m pytest` - Run tests (when implemented)

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

## Plugin System

The application includes a mock plugin system for inventory sources:

- **Nautobot Integration**: Mock connector for Nautobot DCIM
- **CheckMK Integration**: Mock connector for CheckMK monitoring
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