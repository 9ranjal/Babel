/**
 * Transaction Selector Component
 * 
 * Allows users to create new transactions or continue existing ones
 * This is the entry point for the transaction-first architecture
 */
import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Plus, FolderOpen, Users, Calendar } from 'lucide-react';
import { api } from '../lib/apiClient';

interface Transaction {
  id: string;
  name: string | null;
  created_at: string;
  owner_user: string;
}

interface TransactionSelectorProps {
  onTransactionSelect: (transactionId: string) => void;
  selectedTransactionId?: string;
}

export function TransactionSelector({ onTransactionSelect, selectedTransactionId }: TransactionSelectorProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newTransactionName, setNewTransactionName] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/copilot/transactions');
      setTransactions(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  const createTransaction = async () => {
    if (!newTransactionName.trim()) return;
    
    try {
      setLoading(true);
      const response = await api.post('/api/transactions/', {
        name: newTransactionName.trim()
      });
      
      const newTransaction = response.data;
      setTransactions(prev => [newTransaction, ...prev]);
      setNewTransactionName('');
      setShowCreateDialog(false);
      onTransactionSelect(newTransaction.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create transaction');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Transactions</h2>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-indigo-600 hover:bg-indigo-700">
              <Plus className="h-4 w-4 mr-2" />
              New Transaction
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Transaction</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Transaction Name</label>
                <Input
                  placeholder="e.g., Series A Negotiation"
                  value={newTransactionName}
                  onChange={(e) => setNewTransactionName(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={createTransaction}
                  disabled={!newTransactionName.trim() || loading}
                  className="bg-indigo-600 hover:bg-indigo-700"
                >
                  Create
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {loading && transactions.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          Loading transactions...
        </div>
      ) : transactions.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <FolderOpen className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No transactions yet</p>
          <p className="text-sm">Create your first transaction to get started</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {transactions.map((transaction) => (
            <Card 
              key={transaction.id}
              className={`cursor-pointer transition-colors ${
                selectedTransactionId === transaction.id 
                  ? 'ring-2 ring-indigo-500 bg-indigo-50' 
                  : 'hover:bg-gray-50'
              }`}
              onClick={() => onTransactionSelect(transaction.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-gray-900">
                        {transaction.name || 'Untitled Transaction'}
                      </h3>
                      {selectedTransactionId === transaction.id && (
                        <Badge className="bg-indigo-100 text-indigo-700">Active</Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {formatDate(transaction.created_at)}
                      </div>
                      <div className="flex items-center gap-1">
                        <Users className="h-4 w-4" />
                        Transaction
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm">
                    Continue
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default TransactionSelector;
