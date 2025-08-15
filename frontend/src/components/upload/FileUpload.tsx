import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Text, Button, Flex } from '@chakra-ui/react';
import { FiUpload, FiCamera } from 'react-icons/fi';
import receiptService from '../../services/receiptService';
import { Receipt, ReceiptProcessingStatus } from '../../types';

interface FileUploadProps {
  onUploadComplete: (receipt: Receipt) => void;
}

const ACCEPTED_FILE_TYPES = {
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'application/pdf': ['.pdf'],
};

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    
    try {
      setIsUploading(true);
      setUploadProgress(0);
      setErrorMessage(null);
      setSuccessMessage(null);
      
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 300);

      // Upload the file
      const result = await receiptService.uploadReceipt(file);
      clearInterval(progressInterval);
      setUploadProgress(100);

      // Create a receipt object with initial status
      const newReceipt: Receipt = {
        id: result.receiptId,
        fileName: file.name,
        uploadDate: new Date().toISOString(),
        status: ReceiptProcessingStatus.PENDING,
        imageUrl: URL.createObjectURL(file),
      };

      onUploadComplete(newReceipt);
      setSuccessMessage('Receipt uploaded successfully. Review the preview and press Confirm to start processing.');
    } catch (error) {
      console.error('Upload error:', error);
      setErrorMessage('Failed to upload receipt. Please try again.');
    } finally {
      setIsUploading(false);
    }
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
    noClick: true,
    noKeyboard: true,
  });

  // Handle mobile camera capture
  const handleCameraCapture = () => {
    // Open file input with capture attribute
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    fileInput.capture = 'environment'; // Use environment-facing camera
    fileInput.onchange = (e: Event) => {
      const target = e.target as HTMLInputElement;
      if (target.files && target.files.length > 0) {
        onDrop([target.files[0]]);
      }
    };
    fileInput.click();
  };

  return (
    <Box mb={4}>
      <Box
        {...getRootProps()}
        borderWidth={2}
        borderStyle="dashed"
        borderColor={isDragActive ? "blue.400" : "gray.300"}
        borderRadius="md"
        p={6}
        bg={isDragActive ? "blue.50" : "gray.50"}
        textAlign="center"
        transition="all 0.2s"
        _hover={{ borderColor: "blue.300", bg: "blue.50" }}
      >
        <input {...getInputProps()} data-testid="file-input" />
        <Flex direction="column" align="center" justify="center">
          <Text fontSize="40px" color={isDragActive ? "#4299E1" : "#A0AEC0"}>⬆</Text>
          <Text mt={2} fontWeight="medium">
            {isDragActive
              ? "Drop your receipt here"
              : "Drag & drop your receipt here"}
          </Text>
          <Text fontSize="sm" color="gray.500" mt={1} mb={4}>
            JPEG, PNG or PDF (max 10MB)
          </Text>
          
          <Flex>
            <Button
              onClick={open}
              colorPalette="blue"
              size="sm"
              mr={2}
              disabled={isUploading}
            >
              ⬆ Select File
            </Button>
            <Button
              onClick={handleCameraCapture}
              colorPalette="green"
              size="sm"
              disabled={isUploading}
            >
              📷 Take Photo
            </Button>
          </Flex>
        </Flex>
      </Box>
      
      {isUploading && (
        <Box mt={4}>
          <Text mb={1} fontSize="sm">Uploading: {uploadProgress}%</Text>
          <Box
            w="100%"
            h="6px"
            bg="gray.100"
            borderRadius="full"
            overflow="hidden"
          >
            <Box
              w={`${uploadProgress}%`}
              h="100%"
              bg="blue.400"
              transition="width 0.3s ease-in-out"
            />
          </Box>
        </Box>
      )}
      
      {successMessage && (
        <Box mt={4} p={2} bg="green.100" color="green.800" borderRadius="md">
          <Text fontSize="sm">{successMessage}</Text>
        </Box>
      )}
      
      {errorMessage && (
        <Box mt={4} p={2} bg="red.100" color="red.800" borderRadius="md">
          <Text fontSize="sm">{errorMessage}</Text>
        </Box>
      )}
    </Box>
  );
};

export default FileUpload;
