import { createContext, useContext, useEffect, useRef, useCallback } from 'react';
import { WS_SUPPORTED_EVENT_SET } from '../services/websocketContract';

const WebSocketContext = createContext(null);

export const WebSocketProvider = ({ children, token }) => {
  const ws = useRef(null);
  const currentToken = useRef(token || null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = useRef(1000);
  const listeners = useRef({});
  const intentionalClose = useRef(false);

  const closeSocket = useCallback(() => {
    intentionalClose.current = true;
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
  }, []);

  const syncSubscriptions = useCallback(() => {
    if (ws.current?.readyState !== WebSocket.OPEN) {
      return;
    }

    const subscribedEvents = Object.keys(listeners.current);
    if (subscribedEvents.length === 0) {
      return;
    }

    ws.current.send(JSON.stringify({
      action: 'subscribe',
      events: subscribedEvents,
    }));
  }, []);

  const connect = useCallback(() => {
    const activeToken = currentToken.current;
    if (!activeToken) {
      return;
    }

    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const url = `${protocol}//${window.location.host}/ws?token=${activeToken}`;
      
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttempts.current = 0;
        reconnectDelay.current = 1000;
        intentionalClose.current = false;
        syncSubscriptions();
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const eventName = data.event || data.type;
          const payload = data.payload ?? data.data ?? {};

          if (!eventName) {
            return;
          }
          
          if (listeners.current[eventName]) {
            listeners.current[eventName].forEach(callback => callback(payload));
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        if (!intentionalClose.current) {
          attemptReconnect();
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      attemptReconnect();
    }
  }, [syncSubscriptions]);

  const attemptReconnect = useCallback(() => {
    if (reconnectAttempts.current < maxReconnectAttempts) {
      reconnectAttempts.current++;
      setTimeout(() => {
        connect();
      }, reconnectDelay.current);
      reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000);
    }
  }, [connect]);

  useEffect(() => {
    const previousToken = currentToken.current;
    currentToken.current = token || null;

    if (!token) {
      closeSocket();
      reconnectAttempts.current = 0;
      reconnectDelay.current = 1000;
      return () => {};
    }

    const tokenChanged = previousToken && previousToken !== token;
    if (tokenChanged) {
      closeSocket();
    }

    if (token) {
      intentionalClose.current = false;
      connect();
    }

    return () => {
      closeSocket();
    };
  }, [token, connect, closeSocket]);

  const subscribe = useCallback((type, callback) => {
    if (!WS_SUPPORTED_EVENT_SET.has(type)) {
      console.warn(`Subscribing to unknown websocket event: ${type}`);
    }

    if (!listeners.current[type]) {
      listeners.current[type] = [];

      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({
          action: 'subscribe',
          events: [type],
        }));
      }
    }

    listeners.current[type].push(callback);

    return () => {
      listeners.current[type] = listeners.current[type].filter(cb => cb !== callback);

      if (listeners.current[type].length === 0) {
        delete listeners.current[type];
        if (ws.current?.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({
            action: 'unsubscribe',
            events: [type],
          }));
        }
      }
    };
  }, []);

  const send = useCallback((type, payload) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type, payload }));
    }
  }, []);

  const value = {
    isConnected: ws.current?.readyState === WebSocket.OPEN,
    subscribe,
    send,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};
