import React, { useState, useEffect } from 'react';

interface LineItemData {
  id?: number;
  description: string;
  amount: number;
  category_id?: number;
  category_name?: string;
}

interface ReceiptData {
  id: number;
  vendor: string;
  date: string;
  total_amount: number;
  payment_method?: string;
  notes?: string;
  line_items: LineItemData[];
  validation_status?: string;
  confidence_score?: number;
}

interface ReceiptEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  receiptId: number | null;
  onSave?: () => void;
}

const ReceiptEditModal: React.FC<ReceiptEditModalProps> = ({
  isOpen,
  onClose,
  receiptId,
  onSave
}) => {
  const [receipt, setReceipt] = useState<ReceiptData | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadReceipt = async () => {
      if (!receiptId) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // Mock data for now - replace with actual service call
        const mockReceipt: ReceiptData = {
          id: receiptId,
          vendor: 'Sample Store',
          date: '2024-01-15',
          total_amount: 25.99,
          payment_method: 'credit_card',
          notes: 'Sample receipt',
          line_items: [
            {
              id: 1,
              description: 'Coffee',
              amount: 4.99,
              category_id: 1,
              category_name: 'Food & Beverage'
            },
            {
              id: 2,
              description: 'Sandwich',
              amount: 12.99,
              category_id: 1,
              category_name: 'Food & Beverage'
            }
          ],
          validation_status: 'needs_review',
          confidence_score: 0.85
        };
        
        setReceipt(mockReceipt);
      } catch (err) {
        setError('Failed to load receipt');
        console.error('Error loading receipt:', err);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen && receiptId) {
      loadReceipt();
    }
  }, [isOpen, receiptId]);

  const handleSave = async () => {
    if (!receipt) return;
    
    setSaving(true);
    setError(null);
    
    try {
      // Mock save - replace with actual service call
      console.log('Saving receipt:', receipt);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      onSave?.();
      onClose();
    } catch (err) {
      setError('Failed to save receipt');
      console.error('Error saving receipt:', err);
    } finally {
      setSaving(false);
    }
  };

  const updateReceiptField = (field: keyof ReceiptData, value: any) => {
    if (!receipt) return;
    setReceipt(prev => prev ? { ...prev, [field]: value } : null);
  };

  const updateLineItem = (index: number, field: keyof LineItemData, value: any) => {
    if (!receipt) return;
    
    const updatedLineItems = [...receipt.line_items];
    updatedLineItems[index] = { ...updatedLineItems[index], [field]: value };
    
    setReceipt(prev => prev ? { ...prev, line_items: updatedLineItems } : null);
  };

  const addLineItem = () => {
    if (!receipt) return;
    
    const newLineItem: LineItemData = {
      description: '',
      amount: 0,
      category_id: undefined,
      category_name: ''
    };
    
    setReceipt(prev => prev ? {
      ...prev,
      line_items: [...prev.line_items, newLineItem]
    } : null);
  };

  const removeLineItem = (index: number) => {
    if (!receipt) return;
    
    const updatedLineItems = receipt.line_items.filter((_, i) => i !== index);
    setReceipt(prev => prev ? { ...prev, line_items: updatedLineItems } : null);
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000
      }}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '24px',
          maxWidth: '800px',
          width: '90%',
          maxHeight: '90%',
          overflow: 'auto'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>Edit Receipt</h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: '1px solid #ccc',
              borderRadius: '4px',
              padding: '8px 16px',
              cursor: 'pointer'
            }}
          >
            ×
          </button>
        </div>

        {loading && (
          <div style={{ textAlign: 'center', padding: '32px' }}>
            <div>Loading receipt...</div>
          </div>
        )}

        {error && (
          <div
            style={{
              backgroundColor: '#fed7d7',
              border: '1px solid #fc8181',
              borderRadius: '4px',
              padding: '16px',
              marginBottom: '16px',
              color: '#c53030'
            }}
          >
            {error}
          </div>
        )}

        {receipt && !loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Validation Status */}
            {receipt.validation_status && (
              <div>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '8px' }}>
                  Validation Status
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      backgroundColor: receipt.validation_status === 'validated' ? '#c6f6d5' :
                                     receipt.validation_status === 'needs_review' ? '#faf089' : '#fed7d7',
                      color: receipt.validation_status === 'validated' ? '#2f855a' :
                             receipt.validation_status === 'needs_review' ? '#744210' : '#c53030'
                    }}
                  >
                    {receipt.validation_status.replace('_', ' ')}
                  </span>
                  {receipt.confidence_score && (
                    <span style={{ fontSize: '14px' }}>
                      Confidence: {Math.round(receipt.confidence_score * 100)}%
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Basic Receipt Fields */}
            <div>
              <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
                Vendor
              </label>
              <input
                type="text"
                value={receipt.vendor}
                onChange={(e) => updateReceiptField('vendor', e.target.value)}
                placeholder="Vendor name"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>

            <div>
              <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
                Date
              </label>
              <input
                type="date"
                value={receipt.date}
                onChange={(e) => updateReceiptField('date', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>

            <div>
              <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
                Payment Method
              </label>
              <select
                value={receipt.payment_method || ''}
                onChange={(e) => updateReceiptField('payment_method', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              >
                <option value="">Select payment method</option>
                <option value="cash">Cash</option>
                <option value="credit_card">Credit Card</option>
                <option value="debit_card">Debit Card</option>
                <option value="mobile_payment">Mobile Payment</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '14px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
                Notes
              </label>
              <input
                type="text"
                value={receipt.notes || ''}
                onChange={(e) => updateReceiptField('notes', e.target.value)}
                placeholder="Additional notes"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>

            {/* Line Items */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 'bold', margin: 0 }}>Line Items</h3>
                <button
                  onClick={addLineItem}
                  style={{
                    backgroundColor: '#3182ce',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    padding: '8px 16px',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  + Add Item
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {receipt.line_items.map((item, index) => (
                  <div
                    key={index}
                    style={{
                      border: '1px solid #e2e8f0',
                      borderRadius: '4px',
                      padding: '16px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <span style={{ fontWeight: 'bold' }}>Item {index + 1}</span>
                      <button
                        onClick={() => removeLineItem(index)}
                        style={{
                          backgroundColor: '#e53e3e',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          padding: '4px 8px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        Remove
                      </button>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div>
                        <label style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
                          Description
                        </label>
                        <input
                          type="text"
                          value={item.description}
                          onChange={(e) => updateLineItem(index, 'description', e.target.value)}
                          placeholder="Item description"
                          style={{
                            width: '100%',
                            padding: '6px',
                            border: '1px solid #ccc',
                            borderRadius: '4px',
                            fontSize: '14px'
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
                          Amount
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={item.amount}
                          onChange={(e) => updateLineItem(index, 'amount', parseFloat(e.target.value) || 0)}
                          placeholder="0.00"
                          style={{
                            width: '100%',
                            padding: '6px',
                            border: '1px solid #ccc',
                            borderRadius: '4px',
                            fontSize: '14px'
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
                          Category
                        </label>
                        <input
                          type="text"
                          value={item.category_name || ''}
                          onChange={(e) => updateLineItem(index, 'category_name', e.target.value)}
                          placeholder="Category name"
                          style={{
                            width: '100%',
                            padding: '6px',
                            border: '1px solid #ccc',
                            borderRadius: '4px',
                            fontSize: '14px'
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Total */}
              <div
                style={{
                  border: '1px solid #a0aec0',
                  borderRadius: '4px',
                  padding: '16px',
                  backgroundColor: '#f7fafc',
                  marginTop: '16px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 'bold' }}>Total Amount:</span>
                  <span style={{ fontWeight: 'bold', fontSize: '18px' }}>
                    ${receipt.line_items.reduce((sum, item) => sum + item.amount, 0).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', paddingTop: '16px' }}>
              <button
                onClick={onClose}
                style={{
                  backgroundColor: 'white',
                  color: '#4a5568',
                  border: '1px solid #cbd5e0',
                  borderRadius: '4px',
                  padding: '8px 16px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                style={{
                  backgroundColor: saving ? '#a0aec0' : '#3182ce',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '8px 16px',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  fontSize: '14px'
                }}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReceiptEditModal;
