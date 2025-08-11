export interface Wallet {
  id: string;
  mseId: string;
  mseName: string;
  mseCode: string;
  accountNumber: string;
  accountType: 'Business' | 'Savings' | 'Investment' | 'Emergency';
  balance: string;
  currency: string;
  status: 'Active' | 'Inactive' | 'Suspended' | 'Pending';
  lastTransaction: string;
  description: string;
  createdAt: string;
  updatedAt: string;
  transactionCount: number;
  monthlyVolume: string;
}

export interface WalletTransfer {
  fromWalletId: string;
  toWalletId: string;
  amount: string;
  description: string;
  currency: string;
}

export interface WalletTransactionRequest {
  walletId: string;
  type: 'Credit' | 'Debit' | 'Transfer' | 'Withdrawal' | 'Deposit';
  amount: string;
  description: string;
  category?: 'Payment' | 'Purchase' | 'Sale' | 'Transfer' | 'Fee' | 'Refund';
  reference?: string;
}

export interface WalletStatistics {
  totalBalance: string;
  totalWallets: number;
  activeWallets: number;
  monthlyVolume: string;
  monthlyTransactions: number;
  currency: string;
}

export interface WalletFilter {
  status?: 'Active' | 'Inactive' | 'Suspended' | 'Pending';
  accountType?: 'Business' | 'Savings' | 'Investment' | 'Emergency';
  currency?: string;
  dateRange?: {
    start: string;
    end: string;
  };
}

