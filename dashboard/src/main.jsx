import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import { WebSocketProvider } from './context/WebSocketContext.jsx'
import './index.css'

const AppProviders = () => {
  const { token } = useAuth();

  return (
    <WebSocketProvider token={token}>
      <App />
    </WebSocketProvider>
  );
};

const AppWithProviders = () => (
  <AuthProvider>
    <AppProviders />
  </AuthProvider>
);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppWithProviders />
  </React.StrictMode>,
)
