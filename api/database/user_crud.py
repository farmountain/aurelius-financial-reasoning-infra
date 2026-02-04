from sqlalchemy.orm import Session
from database.user_model import User
from security.auth import hash_password, verify_password, generate_user_id
from typing import Optional

class UserDB:
    """Database operations for User model"""

    @staticmethod
    def create(db: Session, email: str, name: str, password: str) -> User:
        """Create a new user"""
        user = User(
            id=generate_user_id(),
            email=email,
            name=name,
            hashed_password=hash_password(password),
            is_active=True,
            is_admin=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def verify_credentials(db: Session, email: str, password: str) -> Optional[User]:
        """Verify user credentials"""
        user = UserDB.get_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def update(db: Session, user_id: str, **kwargs) -> Optional[User]:
        """Update user"""
        user = UserDB.get_by_id(db, user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user_id: str) -> bool:
        """Delete user"""
        user = UserDB.get_by_id(db, user_id)
        if not user:
            return False

        db.delete(user)
        db.commit()
        return True

    @staticmethod
    def list_all(db: Session, limit: int = 100, offset: int = 0) -> list:
        """List all users"""
        return db.query(User).limit(limit).offset(offset).all()
