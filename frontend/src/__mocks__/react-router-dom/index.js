const React = require('react');

// Mock the Router components without JSX to keep Jest config simple
const BrowserRouter = ({ children }) =>
  React.createElement('div', { 'data-testid': 'mock-browser-router' }, children);

const Routes = ({ children }) =>
  React.createElement('div', { 'data-testid': 'mock-routes' }, children);

const Route = ({ path, element }) =>
  React.createElement('div', { 'data-testid': `mock-route-${path}` }, element);

// Mock Navigate component
const Navigate = ({ to }) =>
  React.createElement('div', { 'data-testid': 'mock-navigate', 'data-to': to });

// Mock Link component
const Link = ({ to, children, ...rest }) =>
  React.createElement('a', { href: to, 'data-testid': 'mock-link', ...rest }, children);

// Mock the hooks
const useNavigate = jest.fn().mockReturnValue(jest.fn());
const useLocation = jest.fn().mockReturnValue({ pathname: '/mock-path', search: '', hash: '', state: null });
const useParams = jest.fn().mockReturnValue({});

module.exports = {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Link,
  useNavigate,
  useLocation,
  useParams,
};
