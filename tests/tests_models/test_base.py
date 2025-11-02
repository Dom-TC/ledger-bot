"""Tests for base model."""

import pytest
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ledger_bot.models.base import Base


class TestBase:
    """Test Base model."""

    def test_base_metadata_naming_convention(self):
        """Test that Base has proper naming convention metadata."""
        assert Base.metadata.naming_convention is not None
        assert "ix" in Base.metadata.naming_convention
        assert "uq" in Base.metadata.naming_convention
        assert "ck" in Base.metadata.naming_convention
        assert "fk" in Base.metadata.naming_convention
        assert "pk" in Base.metadata.naming_convention

    def test_base_repr_with_columns(self):
        """Test __repr__ method with a model that has columns."""

        class TestModel(Base):
            __tablename__ = "test_table"
            id: Mapped[int] = mapped_column(Integer, primary_key=True)
            name: Mapped[str] = mapped_column(String)

        # Create instance - will show deferred values
        instance = TestModel()
        repr_str = repr(instance)

        assert "TestModel" in repr_str
        assert "id=" in repr_str
        assert "name=" in repr_str

    def test_base_repr_uninspectable(self):
        """Test __repr__ method returns uninspectable for objects without inspection."""
        from unittest.mock import patch

        from sqlalchemy.exc import NoInspectionAvailable

        class SimpleModel(Base):
            __tablename__ = "simple_table"
            id: Mapped[int] = mapped_column(Integer, primary_key=True)

        instance = SimpleModel()

        # Mock inspect to raise NoInspectionAvailable
        with patch("ledger_bot.models.base.inspect") as mock_inspect:
            mock_inspect.side_effect = NoInspectionAvailable("Test error")
            repr_str = repr(instance)

        assert "SimpleModel" in repr_str
        assert "uninspectable" in repr_str
