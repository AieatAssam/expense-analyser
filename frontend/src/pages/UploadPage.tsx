import React, { useState } from 'react';
import { Box, Container, Heading, Text } from '@chakra-ui/react';
import { useAuth } from '../contexts/AuthContext';
import { ProcessingStatusProvider } from '../contexts/ProcessingStatusContext';
import FileUpload from '../components/upload/FileUpload';
import ReceiptPreview from '../components/preview/ReceiptPreview';
import StatusDisplay from '../components/status/StatusDisplay';
// import UserProfile from '../components/user/UserProfile';
import { Receipt } from '../types';

const UploadPage: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [currentFileName, setCurrentFileName] = useState<string>('');

  const handleUploadComplete = (receipt: Receipt) => {
    // Add receipt to the list
    setReceipts(prev => [receipt, ...prev]);
    
    // Prefer local object URL from upload if available; fallback to placeholder
    setPreviewImage(
      receipt.imageUrl || `https://via.placeholder.com/400x600?text=${encodeURIComponent(receipt.fileName)}`
    );
    setCurrentFileName(receipt.fileName);
  };

  const handlePreviewConfirm = () => {
    // In a real app, you might send the confirmed image to the backend
    setPreviewImage(null);
  };

  const handlePreviewCancel = () => {
    // In a real app, you might need to cancel the upload on the backend
    setPreviewImage(null);
    
    // Remove the last uploaded receipt
    if (receipts.length > 0) {
      setReceipts(prev => prev.slice(1));
    }
  };

  const handleStatusUpdate = (updatedReceipt: Receipt) => {
    setReceipts(prev =>
      prev.map(r => (r.id === updatedReceipt.id ? updatedReceipt : r))
    );
  };

  if (isLoading) {
    return (
      <Container maxW="container.md" py={8}>
        <Text>Loading...</Text>
      </Container>
    );
  }

  if (!isAuthenticated) {
    return (
      <Container maxW="container.md" py={8}>
        <Text>Please log in to upload receipts.</Text>
      </Container>
    );
  }

  return (
    <ProcessingStatusProvider>
      <Container maxW="container.md" py={8}>
        {/* <UserProfile /> */}
        
        <Heading size="lg" mb={6}>Receipt Upload</Heading>

        {previewImage ? (
          <ReceiptPreview
            imageUrl={previewImage}
            fileName={currentFileName}
            onConfirm={handlePreviewConfirm}
            onCancel={handlePreviewCancel}
          />
        ) : (
          <FileUpload onUploadComplete={handleUploadComplete} />
        )}

        {receipts.length > 0 && (
          <Box mt={8}>
            <Heading size="md" mb={4}>Recent Uploads</Heading>
            <Box display="flex" flexDirection="column" gap={4}>
              {receipts.map((receipt) => (
                <StatusDisplay
                  key={receipt.id}
                  receipt={receipt}
                  onStatusUpdate={handleStatusUpdate}
                />
              ))}
            </Box>
          </Box>
        )}

        <Box 
          my={8} 
          height="1px"
          backgroundColor="gray.200"
        />

        <Text fontSize="sm" color="gray.500" textAlign="center">
          Upload your receipt images for automatic expense tracking
        </Text>
      </Container>
    </ProcessingStatusProvider>
  );
};

export default UploadPage;
