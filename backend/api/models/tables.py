from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blob_path: Mapped[str] = mapped_column(Text, nullable=False)
    pages_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    text_plain: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    graph_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    leverage_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime]

    clauses: Mapped[list[Clause]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Clause(Base):
    __tablename__ = "clauses"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    clause_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_idx: Mapped[Optional[int]]
    end_idx: Mapped[Optional[int]]
    page_hint: Mapped[Optional[int]]
    band_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    json_meta: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime]

    document: Mapped[Document] = relationship(back_populates="clauses")
    analyses: Mapped[list[Analysis]] = relationship(back_populates="clause", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    clause_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    band_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    band_score: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    inputs_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    analysis_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    redraft_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime]

    clause: Mapped[Clause] = relationship(back_populates="analyses")


