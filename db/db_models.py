from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, ENUM
from sqlalchemy.orm import declarative_base

Base = declarative_base()


role_enum = ENUM("USER", "ADMIN", "SUPER_ADMIN", name="Role", create_type=False)


class UserDBModel(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id = Column(String, primary_key=True)
    email = Column(String)
    full_name = Column("full_name", String)
    password = Column(String)
    created_at = Column("created_at", DateTime)
    updated_at = Column("updated_at", DateTime)
    verified = Column(Boolean)
    banned = Column(Boolean)
    roles = Column(ARRAY(role_enum))


class MovieDBModel(Base):
    __tablename__ = "movies"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text)
    image_url = Column("image_url", String)
    price = Column(Float)
    location = Column(String)
    published = Column(Boolean)
    genre_id = Column("genre_id", Integer)
    created_at = Column("created_at", DateTime)
    rating = Column(Float)


class GenreDBModel(Base):
    __tablename__ = "genres"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    name = Column(String)
