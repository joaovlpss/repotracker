import datetime
from typing import List, Optional, Set

from sqlalchemy import (
    create_engine,
    Table,
    Column,
    CheckConstraint,
    String,
    ForeignKey,
    DateTime,
    Text,
    Integer,
    UniqueConstraint,
    func,
)

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# We are going to use this base class on our ORM models.
class Base(DeclarativeBase):
    pass


# -- Association Tables --
repository_collaborators_table = Table(
    name="repository_collaborators",
    metadata=Base.metadata,
    include_columns=[
        Column(
            "staff_id",
            Integer,
            ForeignKey("staff.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        Column(
            "repo_id",
            Integer,
            ForeignKey("repository.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    ],
)

issue_labels_table = Table(
    name="issue_labels",
    metadata=Base.metadata,
    include_columns=[
        Column(
            "issue_id",
            Integer,
            ForeignKey("issues.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        Column(
            "label_id",
            Integer,
            ForeignKey("labels.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    ],
)

# -- Main model classes --


class Staff(Base):
    __tablename__ = "staff"

    # We use Mapped[int] so we can keep the attributes' names lowercased and the db column's names uppercased.
    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True)
    name: Mapped[str] = mapped_column("Name", String, unique=True, nullable=False)

    # Relationships
    created_repositories: Mapped[List["Repository"]] = relationship(
        back_populates="creator"
    )
    authored_commits: Mapped[List["Commit"]] = relationship(back_populates="author")
    authored_issues: Mapped[List["Issue"]] = relationship(back_populates="author")
    authored_issue_comments: Mapped[List["IssueComment"]] = relationship(
        back_populates="author"
    )
    assigned_issues: Mapped[List["Issue"]] = relationship(
        secondary=issue_assignees_table, back_populates="assignees"
    )
    collaborating_repositories: Mapped[List["Repository"]] = relationship(
        secondary=repository_collaborators_table, back_populates="collaborators"
    )

    def __repr__(self) -> str:
        return f"<Staff(id={self.id}, name='{self.name}')>"
