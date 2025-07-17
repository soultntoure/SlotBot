
# AI Clinic Assistant Frontend

A modern, professional frontend for an AI-powered clinic appointment assistant. This application provides a clean, calming interface for patients to book appointments, check time slots, and manage their healthcare needs through an intelligent conversational interface.

## Features

- **Professional Medical Design**: Clean, calming aesthetic with medical-appropriate color scheme
- **Conversational Interface**: Chat-based interaction with the AI assistant
- **Quick Actions**: Pre-defined buttons for common tasks (Book appointment, Check slots, Cancel, etc.)
- **Responsive Design**: Fully responsive across desktop, tablet, and mobile devices
- **Real-time Communication**: Seamless integration with backend API
- **Health Check**: Connection status indicator and graceful fallback to demo mode

## API Integration

The frontend integrates with a backend API through the following endpoints:

### Endpoints

- `POST /start_chat` - Initialize a new conversation session
- `POST /chat` - Send messages and receive responses
- `GET /health` - Health check endpoint

### Configuration

Set your backend API URL using environment variables:

```bash
# Copy the example environment file
cp .env.example .env.local

# Edit .env.local and set your API URL
VITE_API_BASE_URL=http://your-backend-url.com
```

## Getting Started

### Prerequisites

- Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

### Installation

```sh
# Clone the repository
git clone <YOUR_GIT_URL>

# Navigate to the project directory
cd <YOUR_PROJECT_NAME>

# Install dependencies
npm install

# Start the development server
npm run dev
```

### Environment Setup

1. Copy `.env.example` to `.env.local`
2. Update `VITE_API_BASE_URL` with your backend API URL
3. Restart the development server

## Project Structure

```
src/
├── pages/
│   ├── Index.tsx          # Main chat interface
│   └── NotFound.tsx       # 404 page
├── components/ui/         # Reusable UI components
├── hooks/                 # Custom React hooks
├── lib/                   # Utility functions
└── index.css             # Global styles
```

## Design System

- **Colors**: Professional blue and indigo gradients with clean whites
- **Typography**: Clean, readable fonts optimized for medical interfaces
- **Layout**: Card-based design with proper spacing and visual hierarchy
- **Interactions**: Smooth animations and hover states for better UX

## Technologies Used

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Shadcn/ui** - High-quality component library
- **Lucide React** - Beautiful icon library
- **Vite** - Fast development and build tool

## Deployment

The application can be deployed to any static hosting service:

### Using Lovable (Recommended)

1. Open your [Lovable Project](https://lovable.dev/projects/d0111350-1f84-4636-9a2e-d87af99be81c)
2. Click the "Publish" button in the top right
3. Your app will be deployed instantly

### Manual Deployment

```sh
# Build for production
npm run build

# The dist/ folder contains your built application
# Upload this folder to your hosting service
```

## Demo Mode

If the backend API is not available, the application gracefully falls back to demo mode, allowing users to interact with the interface and see example responses.

## Support

For support and questions:
- Check the [Lovable Documentation](https://docs.lovable.dev/)
- Join the [Lovable Discord Community](https://discord.com/channels/1119885301872070706/1280461670979993613)

## License

This project is part of the Lovable platform ecosystem.
```
