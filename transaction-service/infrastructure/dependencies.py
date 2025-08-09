"""
Dependency injection container for the application
This is where we wire together the hexagonal architecture components
"""
from functools import lru_cache
from typing import Generator
from sqlalchemy.orm import Session

from domain.services import PaymentService, TransactionService
from adapters.db import DatabaseSessionProvider, DBPaymentRepository, DBTransactionRepository, DBOrderRepository

# Infrastructure layer - session management
_session_provider = DatabaseSessionProvider()

def get_database_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides database sessions.
    This is the only place where FastAPI directly interacts with the database.
    """
    session = _session_provider.get_session()
    try:
        yield session
    finally:
        _session_provider.close_session(session)

# Application layer - service composition
def create_payment_service(db_session: Session) -> PaymentService:
    """
    Factory function to create PaymentService with all its dependencies.
    This is where we compose the hexagonal architecture.
    """
    # Infrastructure adapters (ports implementations)
    transaction_repo = DBTransactionRepository(db_session)
    payment_repo = DBPaymentRepository(db_session)
    
    # Domain service
    return PaymentService(
        transaction_repo=transaction_repo,
        payment_repo=payment_repo
    )

def create_transaction_service(db_session: Session) -> TransactionService:
    """
    Factory function to create TransactionService with all its dependencies.
    """
    # Infrastructure adapters
    transaction_repo = DBTransactionRepository(db_session)
    order_repo = DBOrderRepository(db_session)  # When implemented
    
    # Domain service
    return TransactionService(
        transaction_repo=transaction_repo,
        order_repo=order_repo
    )

# Authentication service placeholder
@lru_cache()
def get_auth_service():
    """
    TODO: Implement proper authentication service
    This should return the actual auth service that validates tokens
    """
    class MockAuthService:
        def get_current_user(self):
            return {"id": 1, "role": "admin"}
    
    return MockAuthService()
