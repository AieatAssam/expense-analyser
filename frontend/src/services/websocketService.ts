// WebSocket service for real-time status updates

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectTimeoutMs: number = 3000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private isConnecting: boolean = false;

  constructor() {
    this.url = `${process.env.REACT_APP_WS_URL || 'ws://localhost:8000'}/ws`;
  }

  // Connect to WebSocket server
  connect(token: string): Promise<boolean> {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return Promise.resolve(true);
    }

    if (this.isConnecting) {
      return new Promise((resolve) => {
        const checkConnected = setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            clearInterval(checkConnected);
            resolve(true);
          }
        }, 100);
      });
    }

    this.isConnecting = true;
    return new Promise((resolve) => {
      try {
        this.ws = new WebSocket(`${this.url}?token=${token}`);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.isConnecting = false;
          resolve(true);
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            const { type, payload } = data;
            
            if (this.listeners.has(type)) {
              this.listeners.get(type)?.forEach(callback => callback(payload));
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.isConnecting = false;
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          resolve(false);
        };
      } catch (error) {
        console.error('Error connecting to WebSocket:', error);
        this.isConnecting = false;
        resolve(false);
      }
    });
  }

  // Subscribe to a specific event type
  subscribe<T>(eventType: string, callback: (data: T) => void): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    
    this.listeners.get(eventType)?.add(callback as (data: any) => void);
    
    // Return unsubscribe function
    return () => {
      this.listeners.get(eventType)?.delete(callback as (data: any) => void);
      if (this.listeners.get(eventType)?.size === 0) {
        this.listeners.delete(eventType);
      }
    };
  }

  // Send message to server
  send(type: string, payload: any): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
      return true;
    }
    return false;
  }

  // Disconnect WebSocket
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // Attempt to reconnect
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
    
    setTimeout(() => {
      const token = localStorage.getItem('auth_token') || '';
      this.connect(token);
    }, this.reconnectTimeoutMs);
  }
}

const websocketService = new WebSocketService();
export default websocketService;
