# Frontend Implementation Documentation

## Overview

The frontend implementation of the Expense Analyser application provides a mobile-friendly web interface for receipt upload and processing with Auth0 integration. The implementation follows a component-based architecture using React and TypeScript.

## Architecture

The frontend is structured around the following key components:

1. **Authentication System**: Auth0 integration with multi-account support
2. **File Upload Interface**: Drag-and-drop and camera capture functionality
3. **Receipt Preview**: Image rotation and confirmation workflow
4. **Processing Status Tracking**: Real-time updates via WebSockets and polling
5. **User Account Management**: Profile display and account switching

## Key Components

### Authentication System

The authentication system is built using Auth0 React SDK and provides:

- User login/logout functionality
- JWT token management for API requests
- Protected routes
- Multi-account support
- Persistent user sessions

Key files:
- `src/contexts/AuthContext.tsx`: Context provider for authentication state
- `src/components/auth/LoginButton.tsx`: Login button component
- `src/components/auth/LogoutButton.tsx`: Logout button component

### File Upload Interface

The file upload interface supports multiple upload methods:

- Drag-and-drop upload
- File selection via browser dialog
- Camera capture for mobile devices

The component validates file types (JPEG, PNG, PDF) and size (max 10MB) before uploading to the backend.

Key files:
- `src/components/upload/FileUpload.tsx`: Main upload component
- `src/services/receiptService.ts`: API integration for receipt uploads

### Receipt Preview

The preview functionality allows users to:

- View uploaded receipts before processing
- Rotate images as needed
- Confirm or cancel uploads

Key files:
- `src/components/preview/ReceiptPreview.tsx`: Preview component with rotation controls

### Processing Status Tracking

The status tracking system provides:

- Real-time updates via WebSockets when available
- Fallback to polling when WebSockets are unavailable
- Visual status indicators (pending, processing, completed, error)
- Error handling with user-friendly messages

Key files:
- `src/contexts/ProcessingStatusContext.tsx`: Context for status management
- `src/components/status/StatusDisplay.tsx`: Status display component
- `src/services/websocketService.ts`: WebSocket client implementation

### User Account Management

The account management features include:

- User profile display
- Account switching for multi-account users
- Basic user settings

Key files:
- `src/components/user/UserProfile.tsx`: User profile component
- `src/components/user/AccountSwitcher.tsx`: Account switching component
- `src/services/userService.ts`: API integration for user management

## Testing Strategy

The frontend implementation includes comprehensive unit tests for all major components:

- Component rendering tests using React Testing Library
- Authentication flow tests with mocked Auth0 responses
- Upload functionality tests with simulated file uploads
- Status tracking tests with mocked WebSocket events and API responses
- User interaction tests for various UI elements

Key test files:
- `src/tests/FileUpload.test.tsx`: Tests for upload functionality
- `src/tests/AuthContext.test.tsx`: Tests for authentication system
- `src/tests/StatusDisplay.test.tsx`: Tests for status tracking

## Environment Configuration

The application uses environment variables for configuration:

- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_WS_URL`: WebSocket URL for real-time updates
- `REACT_APP_AUTH0_DOMAIN`: Auth0 domain
- `REACT_APP_AUTH0_CLIENT_ID`: Auth0 client ID
- `REACT_APP_AUTH0_AUDIENCE`: Auth0 audience

## Deployment Considerations

When deploying the frontend application:

1. Configure Auth0 properly with correct callback URLs
2. Set up environment variables for each deployment environment
3. Enable CORS on the backend API to allow frontend access
4. Configure WebSocket secure connections for production
5. Set up appropriate caching rules for static assets

## Future Enhancements

Potential future enhancements for the frontend:

1. Add offline support with service workers
2. Implement progressive web app capabilities
3. Add receipt history and search functionality
4. Enhance the mobile experience with native-like features
5. Implement user preferences for display options
