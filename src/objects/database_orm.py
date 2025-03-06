from datetime import datetime
from typing import List, Optional


class StaffOrm:
    id: int
    name: str


class CommitOrm:
    id: Optional[int] = None
    author_id: int
    branch_id: int
    comment: str
    date: datetime
    file_changes: int

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Serialize datetime to ISO-8601 format
        }


class BranchOrm:
    id: Optional[int] = None
    name: str
    repo_id: int
    commits: List[CommitOrm] = []


class RepositoryOrm:
    id: Optional[int] = None
    name: str
    author_id: int
    last_commit_date: datetime
    branches: List[BranchOrm] = []

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Serialize datetime to ISO-8601 format
        }
