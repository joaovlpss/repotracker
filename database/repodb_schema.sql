-- Staff table
CREATE TABLE staff (
  ID INTEGER PRIMARY KEY,
  Name TEXT NOT NULL UNIQUE
);

-- Repository table
CREATE TABLE repository (
  ID INTEGER PRIMARY KEY,
  Name TEXT NOT NULL UNIQUE, 
  AuthorID INT NOT NULL REFERENCES staff(ID) ON DELETE CASCADE, 
  LastCommitDate TEXT NOT NULL DEFAULT '1970-01-01 00:00:00' 
);

-- Branch table
CREATE TABLE branch (
  ID INTEGER PRIMARY KEY,
  Name TEXT NOT NULL,
  RepoID INTEGER NOT NULL REFERENCES repository(ID) ON DELETE CASCADE,
  UNIQUE (Name, RepoID) -- Ensure branch names are unique within a repository but not within the whole table.
);

-- Commit table
CREATE TABLE commit (
  ID INTEGER PRIMARY KEY,
  AuthorID INT NOT NULL REFERENCES staff(ID) ON DELETE CASCADE, 
  BranchID INT NOT NULL REFERENCES branch(ID) ON DELETE CASCADE,
  Comment TEXT NOT NULL,
  Date TEXT NOT NULL, -- ISO-8601 format (e.g., '2023-10-01 12:34:56')
  FileChanges INT NOT NULL CHECK (FileChanges >= 0) -- FileChanges should never be negative
);

-- Staff_in_repo table
CREATE TABLE staff_in_repo (
  StaffID INTEGER NOT NULL REFERENCES staff(ID) ON DELETE CASCADE, 
  RepoID INTEGER NOT NULL REFERENCES repository(ID) ON DELETE CASCADE,
  PRIMARY KEY (StaffID, RepoID)
);

-- Indexes for faster lookups
CREATE INDEX idx_repository_AuthorID ON repository(AuthorID);
CREATE INDEX idx_branch_RepoID ON branch(RepoID);
CREATE INDEX idx_commit_BranchID ON commit(BranchID);
CREATE INDEX idx_commit_AuthorID ON commit(AuthorID);
CREATE INDEX idx_staff_in_repo_StaffID ON staff_in_repo(StaffID);
CREATE INDEX idx_staff_in_repo_RepoID ON staff_in_repo(RepoID);

-- Trigger to update LastCommitDate in repository when a new commit is added
CREATE TRIGGER update_last_commit_date
AFTER INSERT ON commit
FOR EACH ROW
BEGIN
  -- Update the LastCommitDate in the repository table
  UPDATE repository
  SET LastCommitDate = NEW.Date
  WHERE ID = (
    SELECT RepoID
    FROM branch
    WHERE ID = NEW.BranchID
  );
END;
