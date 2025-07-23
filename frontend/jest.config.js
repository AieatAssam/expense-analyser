module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
  },
  moduleNameMapper: {
    // Mock CSS imports
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    // Explicitly map module paths
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  // Properly handle ESM modules
  transformIgnorePatterns: [
    'node_modules/(?!(axios|@auth0/auth0-react)/)'
  ],
  setupFilesAfterEnv: [
    '<rootDir>/src/setupTests.ts'
  ],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/'
  ],
  // Display test results with colors
  verbose: true,
  // Allow for jest.spyOn to work properly with React hooks
  restoreMocks: true,
  clearMocks: true,
  resetMocks: false,
};
