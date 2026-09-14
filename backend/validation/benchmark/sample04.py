"""
Bank account class implementation.
"""
from datetime import datetime
from typing import List, Dict, Union

class BankAccount:
    """A simple bank account with basic operations."""
    
    def __init__(self, owner: str, initial_balance: float = 0.0):
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")
        self.owner = owner
        self._balance = initial_balance
        self._transaction_history: List[Dict[str, Union[str, float]]] = []
        self._record_transaction('deposit', initial_balance)
        
    def deposit(self, amount: float) -> float:
        """Deposit money into the account."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self._balance += amount
        self._record_transaction('deposit', amount)
        return self._balance
        
    def withdraw(self, amount: float) -> float:
        """Withdraw money from the account."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount
        self._record_transaction('withdraw', amount)
        return self._balance
        
    def get_balance(self) -> float:
        """Get the current balance."""
        return self._balance
        
    def _record_transaction(self, tx_type: str, amount: float) -> None:
        """Record a transaction in the history."""
        self._transaction_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': tx_type,
            'amount': amount
        })
