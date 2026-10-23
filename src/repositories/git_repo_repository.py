def insert_git_repo(db, rows):
    return db.table("repositories").insert(rows).execute()


def list_git_repos(db, user_id):
    return db.table("repositories").select("*").eq("user_id", user_id).execute()


def delete_git_repo(db, user_id, repo_id):
    return db.table("repositories").delete().eq("user_id", user_id).eq("id", repo_id).execute()
