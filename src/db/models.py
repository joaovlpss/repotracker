import datetime
from typing import List, Optional, Set

from sqlalchemy import (
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
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship


# We are going to use this base class on our ORM models.
class Base(DeclarativeBase):
    pass


# -- Association Classes --

class RepositoryCollaborator(Base):
    __tablename__ = "repository_collaborators"
    staff_id = Column(
        Integer,
        ForeignKey("staff.ID", ondelete="CASCADE"),
        primary_key=True,
    )
    repo_id = Column(
        Integer,
        ForeignKey("repository.ID", ondelete="CASCADE"),
        primary_key=True,
    )
    role = Column(Text, nullable=False, default="collaborator")

    # Relationships back to the main entities
    staff: Mapped["Staff"] = relationship(back_populates="repository_associations")
    repository: Mapped["Repository"] = relationship(
        back_populates="collaborator_associations"
    )

    def __repr__(self) -> str:
        return f"<RepositoryCollaborator(staff_id={self.staff_id}, repo_id={self.repo_id}, role='{self.role}')>"


class IssueLabel(Base):
    __tablename__ = "issue_labels"
    issue_id = Column(
        Integer,
        ForeignKey("issues.ID", ondelete="CASCADE"),
        primary_key=True,
    )
    label_id = Column(
        Integer,
        ForeignKey("labels.ID", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships back to the main entities
    issue: Mapped["Issue"] = relationship(back_populates="label_associations")
    label: Mapped["Label"] = relationship(back_populates="issue_associations")

    def __repr__(self) -> str:
        return f"<IssueLabel(issue_id={self.issue_id}, label_id={self.label_id})>"


class IssueAssignee(Base):
    __tablename__ = "issue_assignees"
    issue_id = Column(
        Integer,
        ForeignKey("issues.ID", ondelete="CASCADE"),
        primary_key=True,
    )
    assignee_id = Column(
        Integer,
        ForeignKey("staff.ID", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships back to the main entities
    issue: Mapped["Issue"] = relationship(back_populates="assignee_associations")
    assignee: Mapped["Staff"] = relationship(back_populates="issue_assignments")

    def __repr__(self) -> str:
        return (
            f"<IssueAssignee(issue_id={self.issue_id}, assignee_id={self.assignee_id})>"
        )


# -- Main model classes --


class Staff(Base):
    __tablename__ = "staff"

    id = Column("ID", Integer, primary_key=True)
    name = Column("Name", String, unique=True, nullable=False)

    # Relationships
    # One-to-Many relationships
    created_repositories: Mapped[List["Repository"]] = relationship(
        back_populates="creator"
    )
    authored_commits: Mapped[List["Commit"]] = relationship(back_populates="author")
    authored_issues: Mapped[List["Issue"]] = relationship(back_populates="author")
    authored_issue_comments: Mapped[List["IssueComment"]] = relationship(
        back_populates="author"
    )

    # Relationships via Association Classes
    # Staff -> RepositoryCollaborator (One-to-Many)
    repository_associations: Mapped[List["RepositoryCollaborator"]] = relationship(
        back_populates="staff"
    )
    # Staff -> IssueAssignee (One-to-Many)
    issue_assignments: Mapped[List["IssueAssignee"]] = relationship(
        back_populates="assignee"
    )

    def __repr__(self) -> str:
        return f"<Staff(id={self.id}, name='{self.name}')>"


class Repository(Base):
    __tablename__ = "repository"

    id = Column("ID", Integer, primary_key=True)
    name = Column("Name", String, unique=True, nullable=False)
    creator_id = Column(
        "CreatorID", ForeignKey("staff.ID", ondelete="CASCADE"), nullable=False
    )
    last_commit_date = Column(
        "LastCommitDate",
        DateTime(timezone=True),
        nullable=False,
        default=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc),
    )

    # Relationships
    # Belongs to one creator (Staff) (Many-to-One)
    creator: Mapped["Staff"] = relationship(back_populates="created_repositories")

    # Has many branches, milestones, issues, labels (One-to-Many)
    branches: Mapped[List["Branch"]] = relationship(
        back_populates="repo", cascade="all, delete-orphan"
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

    # Relationship via Association Class
    # Repository -> RepositoryCollaborator (One-to-Many)
    collaborator_associations: Mapped[List["RepositoryCollaborator"]] = relationship(
        back_populates="repository"
    )

    def __repr__(self) -> str:
        return f"<Repository(id={self.id}, name='{self.name}')>"


class Branch(Base):
    __tablename__ = "branch"

    id = Column("ID", Integer, primary_key=True)
    name = Column("Name", String, nullable=False)
    repo_id = Column(
        "RepoID", ForeignKey("repository.ID", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    # Belongs to a repository (Many-to-One)
    repo: Mapped["Repository"] = relationship(back_populates="branches")
    # Has many commits (One-to-Many)
    commits: Mapped[List["Commit"]] = relationship(
        back_populates="branch", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("Name", "RepoID", name="uq_branch_name_repo"),)

    def __repr__(self) -> str:
        return f"<Branch(id={self.id}, name='{self.name}', repo_id={self.repo_id})>"


class Commit(Base):
    __tablename__ = "commits"

    id = Column("ID", Integer, primary_key=True)
    author_id = Column(
        "AuthorID", ForeignKey("staff.ID", ondelete="CASCADE"), nullable=False
    )
    branch_id = Column(
        "BranchID", ForeignKey("branch.ID", ondelete="CASCADE"), nullable=False
    )
    comment = Column("Comment", Text, nullable=False)
    date = Column("Date", DateTime(timezone=True), nullable=False)
    file_changes = Column("FileChanges", Integer, nullable=False)

    # Relationships (Many-to-One)
    author: Mapped["Staff"] = relationship(back_populates="authored_commits")
    branch: Mapped["Branch"] = relationship(back_populates="commits")

    __table_args__ = (
        CheckConstraint(
            '"FileChanges" >= 0', name="check_commit_filechanges_nonnegative"
        ),
    )

    def __repr__(self) -> str:
        return f"<Commit(id={self.id}, author_id={self.author_id}, branch_id={self.branch_id}, date='{self.date}')>"


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column("ID", Integer, primary_key=True)
    repo_id = Column(
        "RepoID", ForeignKey("repository.ID", ondelete="CASCADE"), nullable=False
    )
    number = Column("Number", Integer, nullable=False)
    title = Column("Title", Text, nullable=False)
    description = Column("Description", Text, nullable=True)
    state = Column("State", String, nullable=False, default="open")
    due_date = Column("DueDate", DateTime, nullable=True)
    created_at = Column(
        "CreatedAt", DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    closed_at = Column("ClosedAt", DateTime(timezone=True), nullable=True)

    # Relationships
    # Belongs to one Repo (Many-to-One)
    repo: Mapped["Repository"] = relationship(back_populates="milestones")
    # Has many issues (One-to-Many)
    issues: Mapped[List["Issue"]] = relationship(back_populates="milestone")

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

    id = Column("ID", Integer, primary_key=True)
    repo_id = Column(
        "RepoID", ForeignKey("repository.ID", ondelete="CASCADE"), nullable=False
    )
    name = Column("Name", String, nullable=False)
    description = Column("Description", Text, nullable=True)
    color = Column("Color", String(6), nullable=True)

    # Relationships
    # Belongs to one Repo (Many-to-One)
    repo: Mapped["Repository"] = relationship("Repository", back_populates="labels")

    # Relationship via Association Class
    # Label -> IssueLabel (One-to-Many)
    issue_associations: Mapped[List["IssueLabel"]] = relationship(
        back_populates="label"
    )


class Issue(Base):
    __tablename__ = "issues"

    id = Column("ID", Integer, primary_key=True)
    repo_id = Column(
        "RepoID", ForeignKey("repository.ID", ondelete="CASCADE"), nullable=False
    )
    milestone_id = Column(
        "MilestoneID", ForeignKey("milestones.ID", ondelete="SET NULL"), nullable=True
    )
    number = Column("Number", Integer, nullable=False)
    title = Column("Title", Text, nullable=False)
    body = Column("Body", Text, nullable=True)
    state = Column("State", String, nullable=False, default="open")
    author_id = Column(
        "AuthorID", ForeignKey("staff.ID", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(
        "CreatedAt", DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        "UpdatedAt", DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    closed_at = Column("ClosedAt", DateTime(timezone=True), nullable=True)

    # Relationships
    # Belongs to one Repo, Milestone (Optional), Author (Many-to-One)
    repo: Mapped["Repository"] = relationship(back_populates="issues")
    milestone: Mapped[Optional["Milestone"]] = relationship(back_populates="issues")
    author: Mapped["Staff"] = relationship(back_populates="authored_issues")

    # Has many comments (One-to-Many)
    comments: Mapped[List["IssueComment"]] = relationship(
        back_populates="issue", cascade="all, delete-orphan"
    )

    # Relationships via Association Classes
    # Issue -> IssueAssignee (One-to-Many)
    assignee_associations: Mapped[List["IssueAssignee"]] = relationship(
        back_populates="issue"
    )
    # Issue -> IssueLabel (One-to-Many)
    label_associations: Mapped[List["IssueLabel"]] = relationship(
        back_populates="issue"
    )

    __table_args__ = (
        UniqueConstraint("RepoID", "Number", name="uq_issue_repo_number"),
        CheckConstraint("\"State\" IN ('open', 'closed')", name="check_issue_state"),
    )

    def __repr__(self) -> str:
        return f"<Issue(id={self.id}, repo_id={self.repo_id}, number={self.number}, title='{self.title[:20]}...')>"


class IssueComment(Base):
    __tablename__ = "issue_comments"

    id = Column("ID", Integer, primary_key=True)
    issue_id = Column(
        "IssueID", ForeignKey("issues.ID", ondelete="CASCADE"), nullable=False
    )
    author_id = Column(
        "AuthorID", ForeignKey("staff.ID", ondelete="CASCADE"), nullable=False
    )
    body = Column("Body", Text, nullable=False)
    created_at = Column(
        "CreatedAt", DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        "UpdatedAt",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships (Many-to-One)
    issue: Mapped["Issue"] = relationship(back_populates="comments")
    author: Mapped["Staff"] = relationship(back_populates="authored_issue_comments")

    def __repr__(self) -> str:
        return f"<IssueComment(id={self.id}, issue_id={self.issue_id}, author_id={self.author_id})>"
