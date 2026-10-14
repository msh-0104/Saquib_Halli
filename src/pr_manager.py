import os
from github import Github

def manage_sync_pull_request(repo_name, branch_name, title, body):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not found.")
        return
        
    g = Github(token)
    repo = g.get_repo(repo_name)
    
    # Check for existing open PRs from this branch (Idempotency)
    existing_prs = repo.get_pulls(state='open', head=f"{repo.owner.login}:{branch_name}")
    
    if existing_prs.totalCount > 0:
        pr = existing_prs[0]
        pr.edit(title=title, body=body)
        print(f"Updated existing pull request: {pr.html_url}")
        return pr.html_url
    else:
        pr = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base="main",
            draft=True
        )
        print(f"Created new draft pull request: {pr.html_url}")
        return pr.html_url
