from models.transaction import Transaction, TransactionType
from functions.database import insert_transaction
from utils.formatting import safe_float


def save_transaction(entry_date, partner, transaction_type, category, subcategory, source, amount, notes=None) -> None:
    transaction = Transaction(
        entry_date=entry_date,
        month=entry_date.strftime("%Y-%m"),
        partner=partner,
        transaction_type=TransactionType(transaction_type),
        category=category,
        subcategory=subcategory or None,
        source=source or None,
        amount=safe_float(amount),
        notes=notes or None,
    )
    insert_transaction(transaction)