module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  transform: {
    '^.+\\.(ts|tsx)$': [
      'ts-jest',
      {
        tsconfig: {
          jsx: 'react-jsx'
        },
        isolatedModules: true,
        useESM: false
      }
    ],
  },
  moduleNameMapper: {
    // CSS and assets
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    // Path alias (if used)
    '^@/(.*)$': '<rootDir>/src/$1',
    // Chakra UI manual mock
    '^@chakra-ui/react$': '<rootDir>/src/__mocks__/@chakra-ui/react.js'
  },
  transformIgnorePatterns: [
    'node_modules/(?!(axios|@auth0/auth0-react)/)'
  ],
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  testPathIgnorePatterns: ['/node_modules/', '/dist/'],
  verbose: true,
  restoreMocks: true,
  clearMocks: true,
  resetMocks: false,
};
