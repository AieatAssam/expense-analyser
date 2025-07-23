const React = require('react');

// Mock the Router components
const BrowserRouter = ({ children }) => <div data-testid="mock-browser-router">{children}</div>;
const Routes = ({ children }) => <div data-testid="mock-routes">{children}</div>;
const Route = ({ path, element }) => <div data-testid={`mock-route-${path}`}>{element}</div>;

// Mock Navigate component
const Navigate = ({ to }) => <div data-testid="mock-navigate" data-to={to} />;

// Mock Link component
const Link = ({ to, children, ...rest }) => (
  <a href={to} data-testid="mock-link" {...rest}>
    {children}
  </a>
);

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
