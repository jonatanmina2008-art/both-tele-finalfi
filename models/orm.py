from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Numeric
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    name = Column(String(255))
    role = Column(String(20), nullable=False) # 'superadmin', 'reseller', 'client'
    created_by = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    suspended_reason = Column(Text)
    avatar_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now() if hasattr(Base, 'metadata') else None)
    updated_at = Column(DateTime(timezone=True), server_default=func.now() if hasattr(Base, 'metadata') else None)

class TenantBot(Base):
    __tablename__ = "tenant_bots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), unique=True)
    bot_token_enc = Column(Text)
    bot_username = Column(String(255))
    bot_name = Column(String(255))
    is_active = Column(Boolean, default=False)
    webhook_url = Column(Text)
