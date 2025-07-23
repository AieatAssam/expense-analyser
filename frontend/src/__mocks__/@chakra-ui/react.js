// Mock for Chakra UI components
const React = require('react');

const mockChakraComponent = (displayName) => {
  const component = React.forwardRef((props, ref) => {
    // Filter out Chakra-specific props that cause warnings
    const safeProps = { ...props };
    
    // List of Chakra UI specific props to filter out
    const chakraProps = [
      'borderWidth', 'borderStyle', 'borderColor', 'borderRadius', 
      'textAlign', 'fontSize', 'fontWeight', 'color', 'bg',
      'p', 'px', 'py', 'pt', 'pr', 'pb', 'pl', 'm', 'mx', 'my', 'mt', 'mr', 'mb', 'ml',
      'w', 'h', 'minW', 'minH', 'maxW', 'maxH', 'size', 'overflow',
      'display', 'flex', 'alignItems', 'justifyContent', 'flexDirection', 'flexWrap',
      'position', 'top', 'right', 'bottom', 'left', 'zIndex',
      'isLoading', 'variant', 'colorScheme', 'aria-label'
    ];
    
    chakraProps.forEach(prop => {
      if (prop in safeProps) {
        delete safeProps[prop];
      }
    });
    
    return React.createElement('div', { 
      ...safeProps,
      ref, 
      'data-testid': props['data-testid'] || `mock-${displayName}`,
      className: [props.className, `mock-${displayName.toLowerCase()}`].filter(Boolean).join(' ')
    }, props.children);
  });
  component.displayName = displayName;
  return component;
};

// Create mock components
const Box = mockChakraComponent('Box');
const Button = mockChakraComponent('Button');
const Container = mockChakraComponent('Container');
const Flex = mockChakraComponent('Flex');
const FormControl = mockChakraComponent('FormControl');
const FormLabel = mockChakraComponent('FormLabel');
const Heading = mockChakraComponent('Heading');
const Image = mockChakraComponent('Image');
const Input = mockChakraComponent('Input');
const Progress = mockChakraComponent('Progress');
const Select = mockChakraComponent('Select');
const Spinner = mockChakraComponent('Spinner');
const Stack = mockChakraComponent('Stack');
const Text = mockChakraComponent('Text');
const VStack = mockChakraComponent('VStack');
const HStack = mockChakraComponent('HStack');
const Alert = mockChakraComponent('Alert');
const AlertIcon = mockChakraComponent('AlertIcon');
const AlertTitle = mockChakraComponent('AlertTitle');
const AlertDescription = mockChakraComponent('AlertDescription');

// Mock hooks
const useToast = jest.fn(() => ({
  // Mock toast methods
  success: jest.fn(),
  error: jest.fn(),
  warning: jest.fn(),
  info: jest.fn(),
  // Generic call method
  __call: jest.fn(),
}));

// Export all the mocked components and hooks
module.exports = {
  Box,
  Button,
  Container,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  Image,
  Input,
  Progress,
  Select,
  Spinner,
  Stack,
  Text,
  VStack,
  HStack,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  useToast,
  ChakraProvider: ({ children }) => React.createElement('div', null, children),
};
