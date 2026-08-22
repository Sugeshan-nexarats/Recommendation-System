from app.models.posts import Post

class PostRepositories:

    def __init__(self,db):
        self.db = db

    def get_all_posts(self):

        all_posts = self.db.query(Post).all()
        print(f"Retrieved {len(all_posts)} posts from DB")
        return all_posts