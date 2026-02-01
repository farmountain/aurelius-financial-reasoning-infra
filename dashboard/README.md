# AURELIUS Dashboard

Web dashboard for the AURELIUS Quant Reasoning Model.

## Features

- **Dashboard Overview**: Real-time statistics and recent activity
- **Strategy Management**: Browse, view details, and generate trading strategies
- **Backtest Analysis**: Visualize backtest results with interactive charts
- **Validation Results**: View walk-forward validation analysis
- **Gate Status**: Monitor dev, CRV, and product gate checks
- **Reflexion Loop**: Track strategy improvement iterations
- **Orchestrator**: Monitor end-to-end pipeline execution

## Tech Stack

- **React 18**: Modern UI library
- **Vite**: Fast build tool and dev server
- **React Router**: Client-side routing
- **TailwindCSS**: Utility-first styling
- **Recharts**: Interactive data visualization
- **Axios**: HTTP client for API calls
- **Lucide React**: Beautiful icon library

## Setup

### Prerequisites

- Node.js 18+ and npm
- AURELIUS REST API running on port 8000

### Installation

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies
npm install
```

### Configuration

Create a `.env` file in the dashboard directory (optional):

```env
VITE_API_URL=http://localhost:8000/api
```

If not specified, the dashboard will use `/api` which is proxied to `http://localhost:8000` in development.

### Development

```bash
# Start development server on port 3000
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

The build output will be in the `dist/` directory.

## Project Structure

```
dashboard/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── Sidebar.jsx
│   │   ├── Header.jsx
│   │   ├── LoadingSpinner.jsx
│   │   ├── ErrorMessage.jsx
│   │   └── EmptyState.jsx
│   ├── pages/           # Page components
│   │   ├── Dashboard.jsx
│   │   ├── Strategies.jsx
│   │   ├── StrategyDetail.jsx
│   │   └── Backtests.jsx
│   ├── services/        # API integration
│   │   └── api.js
│   ├── App.jsx          # Main app component
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── index.html
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── package.json
```

## API Integration

The dashboard communicates with the REST API through the `api.js` service module:

- `strategiesAPI`: Strategy generation and management
- `backtestsAPI`: Backtest execution and results
- `validationsAPI`: Walk-forward validation
- `gatesAPI`: Gate verification checks
- `reflexionAPI`: Reflexion loop iterations
- `orchestratorAPI`: End-to-end pipeline orchestration
- `healthAPI`: API health checks

## Features Implementation Status

- [x] Dashboard overview with stats
- [x] Strategy list and detail views
- [x] Backtest results with charts
- [x] Responsive design
- [x] Loading states and error handling
- [x] Empty states
- [ ] Validation results page
- [ ] Gates status page
- [ ] Reflexion history page
- [ ] Orchestrator runs page
- [ ] Strategy generation form
- [ ] Backtest execution form
- [ ] Real-time updates (WebSocket)
- [ ] Authentication

## Development Notes

### Proxy Configuration

In development, Vite proxies `/api` requests to `http://localhost:8000` (configured in `vite.config.js`). This avoids CORS issues during development.

### Styling

The dashboard uses TailwindCSS with a dark theme optimized for data-heavy interfaces. Custom colors are defined in `tailwind.config.js`.

### Charts

Recharts is used for data visualization. Charts are responsive and styled to match the dark theme.

## Deployment

### Docker

Create a `Dockerfile`:

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

Create `nginx.conf`:

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Contributing

When adding new features:

1. Create components in `src/components/`
2. Create pages in `src/pages/`
3. Add API methods in `src/services/api.js`
4. Update routes in `src/App.jsx`
5. Follow the existing code style and patterns

## License

See LICENSE file in the root directory.
