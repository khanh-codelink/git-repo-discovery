def insert_git_repo(db, rows):
    return db.table("repositories").insert(rows).execute()


def list_git_repos(db, user_id, *, page, per_page, filter=None, sort_by=None):
    query = db.table("repositories").select("*", count="exact").eq("user_id", user_id)
    if filter:
        for key, value in filter.items():
            query = query.eq(key, value)
    if sort_by:
        query = query.order(sort_by)
    if page is not None and per_page is not None:
        query = query.range((page - 1) * per_page, page * per_page - 1)
    return query.execute()


def delete_git_repo(db, user_id, repo_id):
    return db.table("repositories").delete().eq("user_id", user_id).eq("id", repo_id).execute()
