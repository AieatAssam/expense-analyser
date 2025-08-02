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
const Grid = mockChakraComponent('Grid');
const GridItem = mockChakraComponent('GridItem');
const Card = mockChakraComponent('Card');
const CardBody = mockChakraComponent('CardBody');
const CardHeader = mockChakraComponent('CardHeader');
const Stat = mockChakraComponent('Stat');
const StatLabel = mockChakraComponent('StatLabel');
const StatNumber = mockChakraComponent('StatNumber');
const StatHelpText = mockChakraComponent('StatHelpText');
const StatArrow = mockChakraComponent('StatArrow');
const Badge = mockChakraComponent('Badge');
const Avatar = mockChakraComponent('Avatar');
const Menu = mockChakraComponent('Menu');
const MenuButton = mockChakraComponent('MenuButton');
const MenuList = mockChakraComponent('MenuList');
const MenuItem = mockChakraComponent('MenuItem');
const IconButton = mockChakraComponent('IconButton');
const Divider = mockChakraComponent('Divider');
const Skeleton = mockChakraComponent('Skeleton');
const Collapse = mockChakraComponent('Collapse');
const NumberInput = mockChakraComponent('NumberInput');
const NumberInputField = mockChakraComponent('NumberInputField');
const NumberInputStepper = mockChakraComponent('NumberInputStepper');
const NumberIncrementStepper = mockChakraComponent('NumberIncrementStepper');
const NumberDecrementStepper = mockChakraComponent('NumberDecrementStepper');
const InputGroup = mockChakraComponent('InputGroup');
const InputLeftElement = mockChakraComponent('InputLeftElement');
const InputRightElement = mockChakraComponent('InputRightElement');

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

const useBreakpointValue = jest.fn((values) => {
  // Mock implementation that returns the base value or first array item
  if (typeof values === 'object' && values.base !== undefined) {
    return values.base;
  }
  if (Array.isArray(values)) {
    return values[0];
  }
  return values;
});

// Mock disclosure hook
const useDisclosure = jest.fn(() => ({
  isOpen: false,
  onOpen: jest.fn(),
  onClose: jest.fn(),
  onToggle: jest.fn(),
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
  Grid,
  GridItem,
  Card,
  CardBody,
  CardHeader,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Badge,
  Avatar,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  IconButton,
  Divider,
  Skeleton,
  Collapse,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  InputGroup,
  InputLeftElement,
  InputRightElement,
  useToast,
  useBreakpointValue,
  useDisclosure,
  ChakraProvider: ({ children }) => React.createElement('div', null, children),
};
