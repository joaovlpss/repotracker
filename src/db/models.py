import datetime
from typing import List, Optional, Set

from sqlalchemy import (
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
        Column("role", Text, nullable=False, default="collaborator"),
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

issue_assignees_table = Table(
    "issue_assignees",
    Base.metadata,
    Column(
        "issue_id",
        Integer,
        ForeignKey("issues.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "assignee_id",
        Integer,
        ForeignKey("staff.id", ondelete="CASCADE"),
        primary_key=True,
    ),
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


class Repository(Base):
    __tablename__ = "repository"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True)
    name: Mapped[str] = mapped_column("Name", String, unique=True, nullable=False)
    creator_id: Mapped[int] = mapped_column(
        "CreatorID", ForeignKey("staff.id", ondelete="CASCADE"), nullable=False
    )
    last_commit_date: Mapped[datetime.datetime] = mapped_column(
        "LastCommitDate",
        DateTime(timezone=True),
        nullable=False,
        default=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc),
    )

    # Relationships
    # Belongs to one creator (Staff)
    creator: Mapped["Staff"] = relationship(back_populates="created_repositories")

    # Has many branches, collaborators, milestones, issues, labels
    branches: Mapped[List["Branch"]] = relationship(
        back_populates="repo", cascade="all, delete-orphan"
    )
    collaborators: Mapped[List["Staff"]] = relationship(
        secondary=repository_collaborators_table,
        back_populates="collaborating_repositories",
    )
    milestones: Mapped[List["Milestone"]] = relationship(
        back_populates="repo", cascade="all, delete-orphan"
    )
    issues: Mapped[List["Issue"]] = relationship(
        back_populates="repo", cascade="all, delete-orphan"
    )
    labels: Mapped[List["Label"]] = relationship(
        back_populates="repo", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Repository(id={self.id}, name='{self.name}')>"


class Branch(Base):
    __tablename__ = "branch"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True)
    name: Mapped[str] = mapped_column("Name", String, nullable=False)
    repo_id: Mapped[int] = mapped_column(
        "RepoID", ForeignKey("repository.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships

    # Belongs to a repository
    repo: Mapped["Repository"] = relationship(back_populates="branches")

    # Has many commits
    commits: Mapped[List["Commit"]] = relationship(
        back_populates="branch", cascade="all, delete-orphan"
    )

    # A repo cannot have multiple branches of the same name.
    __table_args__ = (UniqueConstraint("Name", "RepoID", name="uq_branch_name_repo"),)

    def __repr__(self) -> str:
        return f"<Branch(id={self.id}, name='{self.name}', repo_id={self.repo_id})>"


class Commit(Base):
    __tablename__ = "commits"  # Note table name difference

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(
        "AuthorID", ForeignKey("staff.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[int] = mapped_column(
        "BranchID", ForeignKey("branch.id", ondelete="CASCADE"), nullable=False
    )
    comment: Mapped[str] = mapped_column(
        "Comment", Text, nullable=False
    )  # Using Text for potentially long messages
    date: Mapped[datetime.datetime] = mapped_column(
        "Date", DateTime(timezone=True), nullable=False
    )
    file_changes: Mapped[int] = mapped_column("FileChanges", Integer, nullable=False)

    # Relationships
    author: Mapped["Staff"] = relationship(back_populates="authored_commits")
    branch: Mapped["Branch"] = relationship(back_populates="commits")

    # A commit may not change a negative amount of files (this should probably never trigger)
    __table_args__ = (
        CheckConstraint(
            '"FileChanges" >= 0', name="check_commit_filechanges_nonnegative"
        ),
    )

    def __repr__(self) -> str:
        return f"<Commit(id={self.id}, author_id={self.author_id}, branch_id={self.branch_id}, date='{self.date}')>"


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True)
    repo_id: Mapped[int] = mapped_column(
        "RepoID", ForeignKey("repository.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(
        "Number", Integer, nullable=False
    )  # GitHub milestone ID for the repo
    title: Mapped[str] = mapped_column("Title", Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(
        "Description", Text, nullable=True
    )
    state: Mapped[str] = mapped_column("State", String, nullable=False, default="open")
    due_date: Mapped[Optional[datetime.date]] = mapped_column(
        "DueDate", DateTime, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        "CreatedAt", DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    closed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        "ClosedAt", DateTime(timezone=True), nullable=True
    )

    # Relationships
    # A milestone can have many issues
    repo: Mapped["Repository"] = relationship(back_populates="milestones")
    issues: Mapped[List["Issue"]] = relationship(back_populates="milestone")

    # A milestone may only have one id.
    # It should also be either open or closed (we won't treat other states for now)
    __table_args__ = (
        UniqueConstraint("RepoID", "Number", name="uq_milestone_repo_number"),
        CheckConstraint(
            "\"State\" IN ('open', 'closed')", name="check_milestone_state"
        ),
    )

    def __repr__(self) -> str:
        return f"<Milestone(id={self.id}, repo_id={self.repo_id}, number={self.number}, title='{self.title[:20]}...')>"


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True)
    repo_id: Mapped[int] = mapped_column(
        "RepoID", ForeignKey("repository.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column("Name", String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(
        "Description", Text, nullable=True
    )
    color: Mapped[Optional[str]] = mapped_column(
        "Color", String(6), nullable=True
    )  # e.g., 'FF0000'

    # Relationships

    # A label is associated with its repo
    repo: Mapped["Repository"] = relationship(back_populates="labels")

    # And it may be present in many issues.
    issues: Mapped[List["Issue"]] = relationship(
        secondary=issue_labels_table, back_populates="labels"
    )

    # Every label name in a repo must be unique.
    __table_args__ = (UniqueConstraint("RepoID", "Name", name="uq_label_repo_name"),)

    def __repr__(self) -> str:
        return f"<Label(id={self.id}, repo_id={self.repo_id}, name='{self.name}')>"


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True)
    repo_id: Mapped[int] = mapped_column(
        "RepoID", ForeignKey("repository.id", ondelete="CASCADE"), nullable=False
    )
    # Using Optional[] for nullable foreign keys, as an issue may not be associated with any Milestone
    milestone_id: Mapped[Optional[int]] = mapped_column(
        "MilestoneID", ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True
    )
    number: Mapped[int] = mapped_column(
        "Number", Integer, nullable=False
    )  # GitHub issue number for the repo
    title: Mapped[str] = mapped_column("Title", Text, nullable=False)
    body: Mapped[Optional[str]] = mapped_column("Body", Text, nullable=True)
    state: Mapped[str] = mapped_column("State", String, nullable=False, default="open")
    # Assuming issues always have an author
    author_id: Mapped[int] = mapped_column(
        "AuthorID", ForeignKey("staff.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        "CreatedAt", DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        "UpdatedAt", DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    closed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        "ClosedAt", DateTime(timezone=True), nullable=True
    )

    # Relationships

    repo: Mapped["Repository"] = relationship(back_populates="issues")
    milestone: Mapped[Optional["Milestone"]] = relationship(back_populates="issues")
    # And has one author
    author: Mapped["Staff"] = relationship(back_populates="authored_issues")

    # But many assignees (potentially), labels and comments.
    assignees: Mapped[List["Staff"]] = relationship(
        secondary=issue_assignees_table, back_populates="assigned_issues"
    )
    labels: Mapped[List["Label"]] = relationship(
        secondary=issue_labels_table, back_populates="issues"
    )
    comments: Mapped[List["IssueComment"]] = relationship(
        back_populates="issue", cascade="all, delete-orphan"
    )

    # Sane constraints for uniqueness and state consistency
    __table_args__ = (
        UniqueConstraint("RepoID", "Number", name="uq_issue_repo_number"),
        CheckConstraint("\"State\" IN ('open', 'closed')", name="check_issue_state"),
    )

    def __repr__(self) -> str:
        return f"<Issue(id={self.id}, repo_id={self.repo_id}, number={self.number}, title='{self.title[:20]}...')>"


class IssueComment(Base):
    __tablename__ = "issue_comments"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(
        "IssueID", ForeignKey("issues.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        "AuthorID", ForeignKey("staff.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column("Body", Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        "CreatedAt", DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        "UpdatedAt",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    issue: Mapped["Issue"] = relationship(back_populates="comments")
    author: Mapped["Staff"] = relationship(back_populates="authored_issue_comments")

    def __repr__(self) -> str:
        return f"<IssueComment(id={self.id}, issue_id={self.issue_id}, author_id={self.author_id})>"
