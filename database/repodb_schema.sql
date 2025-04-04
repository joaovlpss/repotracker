-- Staff table
CREATE TABLE staff (
  ID SERIAL PRIMARY KEY,
  Name TEXT NOT NULL UNIQUE
);

-- Repository table
CREATE TABLE repository (
  ID SERIAL PRIMARY KEY,
  Name TEXT NOT NULL UNIQUE,
  CreatorID INT NOT NULL REFERENCES staff(ID) ON DELETE CASCADE,
  -- Use TIMESTAMPTZ for accurate time zone handling
  LastCommitDate TIMESTAMPTZ NOT NULL DEFAULT '1970-01-01 00:00:00+00'
);

-- Branch table
CREATE TABLE branch (
  ID SERIAL PRIMARY KEY,
  Name TEXT NOT NULL,
  RepoID INTEGER NOT NULL REFERENCES repository(ID) ON DELETE CASCADE,
  UNIQUE (Name, RepoID)
);

-- Commit table
CREATE TABLE commits (
  ID SERIAL PRIMARY KEY,
  AuthorID INT NOT NULL REFERENCES staff(ID) ON DELETE CASCADE,
  BranchID INT NOT NULL REFERENCES branch(ID) ON DELETE CASCADE,
  Comment TEXT NOT NULL,
  -- Use TIMESTAMPTZ for commit timestamps
  Date TIMESTAMPTZ NOT NULL,
  FileChanges INT NOT NULL CHECK (FileChanges >= 0)
);

-- Repository Collaborators table
CREATE TABLE repository_collaborators (
  StaffID INTEGER NOT NULL REFERENCES staff(ID) ON DELETE CASCADE,
  RepoID INTEGER NOT NULL REFERENCES repository(ID) ON DELETE CASCADE,
  PRIMARY KEY (StaffID, RepoID)
);

-- Milestones table
CREATE TABLE milestones (
    ID SERIAL PRIMARY KEY,
    RepoID INTEGER NOT NULL REFERENCES repository(ID) ON DELETE CASCADE,
    Number INTEGER NOT NULL,
    Title TEXT NOT NULL,
    Description TEXT,
    State TEXT NOT NULL DEFAULT 'open' CHECK (State IN ('open', 'closed')),
    -- Use DATE for due dates without time component
    DueDate DATE,
    CreatedAt TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ClosedAt TIMESTAMPTZ,
    UNIQUE(RepoID, Number)
);

-- Issues table
CREATE TABLE issues (
    ID SERIAL PRIMARY KEY,
    RepoID INTEGER NOT NULL REFERENCES repository(ID) ON DELETE CASCADE,
    MilestoneID INTEGER REFERENCES milestones(ID) ON DELETE SET NULL,
    Number INTEGER NOT NULL,
    Title TEXT NOT NULL,
    Body TEXT,
    State TEXT NOT NULL DEFAULT 'open' CHECK (State IN ('open', 'closed')),
    AuthorID INTEGER NOT NULL REFERENCES staff(ID) ON DELETE CASCADE,
    CreatedAt TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ClosedAt TIMESTAMPTZ,
    UNIQUE(RepoID, Number)
);

-- Issue Assignees table
CREATE TABLE issue_assignees (
    IssueID INTEGER NOT NULL REFERENCES issues(ID) ON DELETE CASCADE,
    AssigneeID INTEGER NOT NULL REFERENCES staff(ID) ON DELETE CASCADE,
    PRIMARY KEY (IssueID, AssigneeID)
);

-- Labels table
CREATE TABLE labels (
    ID SERIAL PRIMARY KEY,
    RepoID INTEGER NOT NULL REFERENCES repository(ID) ON DELETE CASCADE,
    Name TEXT NOT NULL,
    Description TEXT,
    Color TEXT, -- e.g., 'FF0000'
    UNIQUE(RepoID, Name)
);

-- Issue Labels table
CREATE TABLE issue_labels (
    IssueID INTEGER NOT NULL REFERENCES issues(ID) ON DELETE CASCADE,
    LabelID INTEGER NOT NULL REFERENCES labels(ID) ON DELETE CASCADE,
    PRIMARY KEY (IssueID, LabelID)
);

-- Issue Comments table
CREATE TABLE issue_comments (
    ID SERIAL PRIMARY KEY,
    IssueID INTEGER NOT NULL REFERENCES issues(ID) ON DELETE CASCADE,
    AuthorID INTEGER NOT NULL REFERENCES staff(ID) ON DELETE CASCADE,
    Body TEXT NOT NULL,
    CreatedAt TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_repository_CreatorID ON repository(CreatorID);
CREATE INDEX idx_branch_RepoID ON branch(RepoID);
CREATE INDEX idx_commit_BranchID ON commits(BranchID);
CREATE INDEX idx_commit_AuthorID ON commits(AuthorID);
CREATE INDEX idx_repo_collab_StaffID ON repository_collaborators(StaffID);
CREATE INDEX idx_repo_collab_RepoID ON repository_collaborators(RepoID);
CREATE INDEX idx_milestones_RepoID ON milestones(RepoID);
CREATE INDEX idx_issues_RepoID ON issues(RepoID);
CREATE INDEX idx_issues_AuthorID ON issues(AuthorID);
CREATE INDEX idx_issues_MilestoneID ON issues(MilestoneID);
CREATE INDEX idx_issue_assignees_IssueID ON issue_assignees(IssueID);
CREATE INDEX idx_issue_assignees_AssigneeID ON issue_assignees(AssigneeID);
CREATE INDEX idx_labels_RepoID ON labels(RepoID);
CREATE INDEX idx_issue_labels_IssueID ON issue_labels(IssueID);
CREATE INDEX idx_issue_labels_LabelID ON issue_labels(LabelID);
CREATE INDEX idx_issue_comments_IssueID ON issue_comments(IssueID);
CREATE INDEX idx_issue_comments_AuthorID ON issue_comments(AuthorID);


-- Triggers

-- Trigger function to update LastCommitDate in repository
CREATE OR REPLACE FUNCTION fn_update_repo_last_commit()
RETURNS TRIGGER AS $$
DECLARE
  repo_id_to_update INT;
BEGIN
  -- Find the RepoID associated with the commit's branch
  SELECT RepoID INTO repo_id_to_update
  FROM branch
  WHERE ID = NEW.BranchID;

  -- Update the repository table if the new commit date is later
  UPDATE repository
  SET LastCommitDate = NEW.Date
  WHERE ID = repo_id_to_update AND LastCommitDate < NEW.Date;

  RETURN NULL; -- Result is ignored since this is an AFTER trigger
END;
$$ LANGUAGE plpgsql;

-- Trigger definition
CREATE TRIGGER trg_update_last_commit_date
AFTER INSERT ON commits
FOR EACH ROW
EXECUTE FUNCTION fn_update_repo_last_commit();


-- Trigger function to automatically update the 'UpdatedAt' timestamp on issue modification
CREATE OR REPLACE FUNCTION fn_update_issue_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.UpdatedAt = CURRENT_TIMESTAMP;
   RETURN NEW; -- Return the modified row to be inserted/updated
END;
$$ LANGUAGE plpgsql;

-- Trigger definition (BEFORE UPDATE)
CREATE TRIGGER trg_update_issue_timestamp
BEFORE UPDATE ON issues
FOR EACH ROW
EXECUTE FUNCTION fn_update_issue_timestamp();


--Trigger function to add repository creator as an initial 'Owner' collaborator
CREATE OR REPLACE FUNCTION fn_add_repo_creator()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO repository_collaborators (StaffID, RepoID, Role)
  VALUES (NEW.CreatorID, NEW.ID);
  RETURN NULL; -- Result is ignored since this is an AFTER trigger
END;
$$ LANGUAGE plpgsql;

-- Trigger definition
CREATE TRIGGER trg_add_repo_creator_as_collaborator
AFTER INSERT ON repository
FOR EACH ROW
EXECUTE FUNCTION fn_add_repo_creator();