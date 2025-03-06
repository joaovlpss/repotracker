from datetime import datetime
from typing import List, Optional


class StaffOrm:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name


class CommitOrm:
    def __init__(
        self,
        author_id: int,
        branch_id: int,
        comment: str,
        date: datetime,
        file_changes: int,
        id: Optional[int] = None,
    ):
        self.id = id
        self.author_id = author_id
        self.branch_id = branch_id
        self.comment = comment
        self.date = date
        self.file_changes = file_changes

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Serialize datetime to ISO-8601 format
        }


class BranchOrm:
    def __init__(
        self,
        name: str,
        repo_id: int,
        commits: List[CommitOrm] | None = None,
        id: Optional[int] = None,
    ):
        self.id = id
        self.name = name
        self.repo_id = repo_id
        self.commits = commits if commits is not None else []


class RepositoryOrm:
    def __init__(
        self,
        name: str,
        author_id: int,
        last_commit_date: datetime,
        branches: List[BranchOrm] | None = None,
        id: Optional[int] = None,
    ):
        self.id = id
        self.name = name
        self.author_id = author_id
        self.last_commit_date = last_commit_date
        self.branches = branches if branches is not None else []

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Serialize datetime to ISO-8601 format
        }
