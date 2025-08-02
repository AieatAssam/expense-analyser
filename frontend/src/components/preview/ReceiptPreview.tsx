import React, { useState } from 'react';
import { Box, Text, Button, Flex, Image } from '@chakra-ui/react';
import { FiRotateCw, FiRotateCcw, FiCheck, FiX } from 'react-icons/fi';

interface ReceiptPreviewProps {
  imageUrl: string;
  fileName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

const ReceiptPreview: React.FC<ReceiptPreviewProps> = ({
  imageUrl,
  fileName,
  onConfirm,
  onCancel,
}) => {
  const [rotation, setRotation] = useState(0);

  const rotateClockwise = () => {
    setRotation((prev) => (prev + 90) % 360);
  };

  const rotateCounterClockwise = () => {
    setRotation((prev) => (prev - 90 + 360) % 360);
  };

  return (
    <Box
      borderWidth={1}
      borderStyle="solid"
      borderColor="gray.200"
      borderRadius="md"
      p={4}
      bg="white"
    >
      <Text fontWeight="medium" mb={2}>
        Preview: {fileName}
      </Text>

      <Box
        position="relative"
        w="100%"
        h="300px"
        overflow="hidden"
        bg="gray.100"
        borderRadius="md"
        mb={4}
      >
        <Image
          src={imageUrl}
          alt="Receipt preview"
          objectFit="contain"
          w="100%"
          h="100%"
          transform={`rotate(${rotation}deg)`}
          transition="transform 0.3s ease"
        />
      </Box>

      <Flex justify="space-between">
        <Flex>
          <Button
            onClick={rotateCounterClockwise}
            size="sm"
            mr={2}
            aria-label="Rotate counter-clockwise"
          >
            ↺
          </Button>
          <Button
            onClick={rotateClockwise}
            size="sm"
            aria-label="Rotate clockwise"
          >
            ↻
          </Button>
        </Flex>

        <Flex>
          <Button
            onClick={onCancel}
            size="sm"
            mr={2}
            variant="outline"
          >
            × Cancel
          </Button>
          <Button
            onClick={onConfirm}
            colorPalette="green"
            size="sm"
          >
            ✓ Confirm
          </Button>
        </Flex>
      </Flex>
    </Box>
  );
};

export default ReceiptPreview;
