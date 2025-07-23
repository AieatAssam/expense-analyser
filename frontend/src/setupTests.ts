// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Global mocks are now in __mocks__ directory
// This allows us to avoid any JSX in the setupTests file

// Setup global mocks for browser APIs that might be missing in jsdom
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock the WebSocket API
class MockWebSocket {
  onopen = null;
  onclose = null;
  onmessage = null;
  onerror = null;
  url = '';
  readyState = 0;
  send = jest.fn();
  close = jest.fn();
  
  constructor(url: string) {
    this.url = url;
  }
}

global.WebSocket = MockWebSocket as any;

// Mock console methods to keep tests clean
const originalConsoleError = console.error;
console.error = (...args) => {
  // Filter out React-specific warnings that might pollute test output
  if (
    args[0] && 
    typeof args[0] === 'string' && 
    (args[0].includes('Warning:') || 
     args[0].includes('Error:'))
  ) {
    return;
  }
  originalConsoleError(...args);
};
