import os
import sqlite3
import json
import git
from database_orm import CommitOrm, RepositoryOrm
from datetime import datetime
from pydantic import BaseModel


class RepositoryManager(BaseModel):
    db_connection: sqlite3.Connection
    repository_list: list[git.Repo]

    def __init__(self, db_file_path: str, repo_json_path: str):
        self.db_connection = self.get_connection(db_file_path)
        self.repository_list = self.load_tracked_repos(repo_json_path)

    def get_connection(self, db_file_path: str) -> sqlite3.Connection:
        return sqlite3.connect(db_file_path)

    def load_tracked_repos(self, repo_json_path: str) -> list[git.Repo]:
        """
        Populate the repository_list and create new repository entries
        in the database if there are new repositories in the json list.
        """
        repos: list[git.Repo] = []

        # First, we open our JSON list.
        with open(repo_json_path) as dictionary:
            data = json.load(dictionary)

        for repo in data["repositories"]:
            repo_name = repo["name"]
            repo_url = repo["ssh_url"]
            repo_path = "./tracked_repos" + repo_name

            # If this repo isn't downloaded yet, we should clone it.
            if repo_name not in os.listdir("./tracked_repos"):
                new_repo = git.Repo.clone_from(repo_url, repo_path, branch="main")
                self._create_repo(new_repo)

            # We add the path to our repo to our list.
            repos.append(git.Repo(repo_path))

        # Finally, we return all our repos.
        return repos

    def update_repository(self, repository: git.Repo):
        """
        Update the database with the latest branches and commits from the repository.
        """
        # Get the repository's name and last commit date from the database
        repo_name = os.path.basename(repository.working_dir)
        last_commit_date = self._get_last_commit_date(repo_name)

        # Fetch all branches in the repository
        branches = repository.branches

        # Iterate over each branch and fetch new commits
        for branch in branches:
            # Check if the branch exists in the database
            branch_id = self._get_or_create_branch(repo_name, branch.name)

            # Fetch new commits in this branch (after last_commit_date)
            new_commits = self._get_new_commits(repository, branch, last_commit_date)

            # Insert new commits into the database
            for commit in new_commits:
                self._insert_commit(branch_id, commit)

        # Update the repository's LastCommitDate in the database
        self._update_last_commit_date(repo_name, datetime.now())

    def _create_repo(self, repo: git.Repo) -> RepositoryOrm:
        """
        Create a RepositoryOrm object from a git.Repo and insert it into the database.
        """
        # Extract repository name from the working directory
        repo_name = os.path.basename(repo.working_dir)

        # Get the default branch (usually 'main' or 'master')
        default_branch = repo.active_branch.name

        # Get the author of the repository (assume the first commit author is the repository author)
        first_commit = next(repo.iter_commits(default_branch))
        author_name = first_commit.author.name

        # Get or create the staff member in the database
        author_id = self._get_or_create_staff(author_name)

        # Create a RepositoryOrm object
        repo_orm = RepositoryOrm(
            name=repo_name,
            author_id=author_id,
            last_commit_date=datetime.min,  # Initialize with the earliest possible date
            branches=[],  # Branches will be added later
        )

        # Insert the repository into the database
        cursor = self.db_connection.cursor()
        cursor.execute(
            "INSERT INTO repository (Name, AuthorID, LastCommitDate) VALUES (?, ?, ?)",
            (repo_orm.name, repo_orm.author_id, repo_orm.last_commit_date.isoformat()),
        )
        self.db_connection.commit()

        # Set the repository ID (assigned by the database)
        repo_orm.id = cursor.lastrowid

        return repo_orm

    def _get_last_commit_date(self, repo_name: str) -> datetime:
        """
        Get the LastCommitDate for the repository from the database.
        """
        cursor = self.db_connection.cursor()
        cursor.execute(
            "SELECT LastCommitDate FROM repository WHERE Name = ?", (repo_name,)
        )
        result = cursor.fetchone()
        return datetime.fromisoformat(result[0]) if result else datetime.min

    def _get_or_create_branch(self, repo_name: str, branch_name: str) -> int | None:
        """
        Get the branch ID from the database if it exists, or create a new branch.
        """
        cursor = self.db_connection.cursor()
        cursor.execute(
            "SELECT ID FROM branch WHERE Name = ? AND RepoID = (SELECT ID FROM repository WHERE Name = ?)",
            (branch_name, repo_name),
        )
        result = cursor.fetchone()

        if result:
            return result[0]  # Return existing branch ID
        else:
            # Insert new branch
            cursor.execute(
                "INSERT INTO branch (Name, RepoID) VALUES (?, (SELECT ID FROM repository WHERE Name = ?))",
                (branch_name, repo_name),
            )
            self.db_connection.commit()
            return cursor.lastrowid  # Return new branch ID

    def _insert_commit(self, branch_id: int | None, commit: CommitOrm):
        """
        Insert a commit into the database.
        """
        cursor = self.db_connection.cursor()
        cursor.execute(
            "INSERT INTO commit (AuthorID, BranchID, Comment, Date, FileChanges) VALUES (?, ?, ?, ?, ?)",
            (
                commit.author_id,
                branch_id,
                commit.comment,
                commit.date.isoformat(),
                commit.file_changes,
            ),
        )
        self.db_connection.commit()

    def _update_last_commit_date(self, repo_name: str, last_commit_date: datetime):
        """
        Update the LastCommitDate for the repository in the database.
        """
        cursor = self.db_connection.cursor()
        cursor.execute(
            "UPDATE repository SET LastCommitDate = ? WHERE Name = ?",
            (last_commit_date.isoformat(), repo_name),
        )
        self.db_connection.commit()

    def _get_or_create_staff(self, author_name: str | None) -> int:
        """
        Get the staff ID from the database if it exists, or create a new staff member.
        """
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT ID FROM staff WHERE Name = ?", (author_name,))
        result = cursor.fetchone()

        if result:
            return result[0]  # Return existing staff ID
        else:
            # Insert new staff
            cursor.execute("INSERT INTO staff (Name) VALUES (?)", (author_name,))
            self.db_connection.commit()
            return cursor.lastrowid  # Return new staff ID

    def _get_new_commits(
        self, repository: git.Repo, branch, last_commit_date: datetime
    ) -> list[CommitOrm]:
        """
        Fetch new commits in the branch that are newer than last_commit_date.
        """
        new_commits = []
        repo_name = os.path.basename(repository.working_dir)

        for commit in repository.iter_commits(branch):
            branch_name = branch.name

            commit_date = datetime.fromtimestamp(commit.committed_date)
            if commit_date > last_commit_date:
                new_commits.append(
                    CommitOrm(
                        author_id=self._get_or_create_staff(commit.author.name),
                        branch_id=self._get_or_create_branch(repo_name, branch_name),
                        comment=commit.message,
                        date=commit_date,
                        file_changes=len(commit.stats.files),
                    )
                )
            else:
                break  # Stop iterating once we reach old commits
        return new_commits
