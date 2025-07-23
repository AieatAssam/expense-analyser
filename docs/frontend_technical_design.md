# Frontend Technical Design Document

## System Architecture

### Overview

The Expense Analyser frontend is a React-based web application that provides a mobile-friendly interface for receipt upload and processing. It integrates with the backend API for data persistence and processing, uses Auth0 for authentication, and implements WebSockets for real-time updates.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend Client                     │
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌────────────────────────┐   │
│  │ React UI │  │ Context │  │ Services              │   │
│  │ Components  │ Providers│  │ - API Client         │   │
│  │         │  │         │  │ - WebSocket Client    │   │
│  └─────────┘  └─────────┘  │ - Auth Service        │   │
│                            └────────────────────────┘   │
└───────────────────────────────┬─────────────────────────┘
                                │
                                ▼
┌──────────────────────┐    ┌────────────┐    ┌────────────┐
│     Auth0 Service    │    │ Backend API│    │ WebSocket  │
│                      │◄───►│            │◄───►│ Server    │
└──────────────────────┘    └────────────┘    └────────────┘
```

## Component Architecture

The frontend uses a component-based architecture organized by feature:

### Core Components

1. **App**: Root component that sets up routing and global providers
2. **Pages**: Container components representing distinct application views
3. **Context Providers**: Global state management for authentication and processing status
4. **Services**: API clients for backend communication
5. **Components**: Reusable UI components organized by feature

### Component Hierarchy

```
App
├── AuthProvider
│   └── UserProfile
│       └── AccountSwitcher
├── ProcessingStatusProvider
└── Pages
    └── UploadPage
        ├── FileUpload
        ├── ReceiptPreview
        └── StatusDisplay
```

## State Management

The application uses React Context for global state management:

### Auth Context

- User authentication state
- JWT token management
- User profile information
- Multi-account state

### Processing Status Context

- Real-time receipt processing status
- WebSocket connection state
- Status messages and errors

## Authentication Flow

1. User clicks "Login" button
2. Auth0 login page is displayed
3. User authenticates with Auth0
4. Auth0 redirects back with access token
5. Token is stored and used for API requests
6. User profile is fetched from backend API
7. Auth context is updated with user data

## File Upload Flow

1. User selects a file via drag-drop, file selection, or camera
2. Client validates file type and size
3. File is uploaded to backend API
4. Backend returns receipt ID and status
5. Client displays preview or processing status
6. WebSocket connection provides real-time status updates
7. Status display is updated as processing progresses

## WebSocket Integration

The application uses WebSockets for real-time updates:

1. Client connects to WebSocket server after authentication
2. Client subscribes to receipt status events
3. Server pushes status updates as receipt processing progresses
4. Client updates UI based on received events
5. Client falls back to polling if WebSocket connection fails

## API Integration

The application interacts with the backend API through service modules:

### Receipt Service

- `uploadReceipt(file)`: Upload a receipt file
- `getReceiptById(id)`: Get receipt details
- `getReceiptStatus(id)`: Get processing status
- `listReceipts(page, limit)`: List user's receipts

### User Service

- `getUserProfile()`: Get user profile with accounts
- `switchAccount(accountId)`: Switch active account
- `getAccounts()`: Get user's accounts list

## Responsive Design

The application implements a mobile-first responsive design:

- Flexible layouts using CSS flexbox
- Optimized for touch interactions on mobile
- Responsive image handling
- Camera integration for mobile devices
- Simplified UI for smaller screens

## Error Handling

The application implements comprehensive error handling:

- API error handling with user-friendly messages
- WebSocket connection error recovery
- File validation errors with clear feedback
- Processing error display with retry options
- Auth0 authentication error handling

## Security Considerations

- JWT tokens for API authentication
- Secure token storage
- HTTPS for all API communication
- WebSocket authentication
- File validation to prevent malicious uploads
- Auth0 integration for secure authentication

## Testing Strategy

The application includes comprehensive unit tests for all major components:

- Component rendering tests
- Authentication flow tests
- Upload functionality tests
- Status tracking tests
- User interaction tests

## Performance Optimizations

- React component memoization
- Lazy loading of non-critical components
- Optimized image handling
- WebSocket for efficient real-time updates
- API response caching when appropriate

## Deployment Strategy

The frontend is built as a static web application that can be deployed to any static hosting service:

1. Build the React application for production
2. Deploy static assets to web server or CDN
3. Configure environment variables for production
4. Set up proper CORS headers on the backend
5. Configure Auth0 for production domains
