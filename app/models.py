# 所有的实体类
from . import db

# 用户信息


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    loginname = db.Column(db.String(30), nullable=False)
    nickname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(30), nullable=False)
    head_link = db.Column(db.String(255))
    music_like = db.Column(db.Text)
    story_history = db.Column(db.Text)

    # 通过用户查帖子
    topics = db.relationship("Topic", backref="user", lazy="dynamic")
    # 查用户的回复
    replys = db.relationship("Reply", backref="user", lazy="dynamic")
    # 通过用户查评论
    comments = db.relationship("Comment", backref="user", lazy="dynamic")


# 用户发的帖子
class Topic(db.Model):
    __tablename__ = "topic"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False)
    read_num = db.Column(db.Integer, default=0)
    content = db.Column(db.Text)
    images = db.Column(db.Text)

    # 发表用户
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # 主题类型
    type_id = db.Column(db.Integer, db.ForeignKey("topicType.id"))
    # 回复的评论
    comments = db.relationship("Comment", backref="topic", lazy="dynamic")
    # 查询点赞的用户 Topic.vokeusers.
    vokeusers = db.relationship(
        "User",
        secondary="voke",
        lazy="dynamic",
        backref=db.backref("voke_topic", lazy="dynamic"))

    def __repr__(self):
        return "<{}>".format(self.title)

# 用户发的帖子类型


class TopicType(db.Model):
    __tablename__ = "topicType"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(30), nullable=False)
    # 通过类型查帖子
    topics = db.relationship("Topic", backref="topicType", lazy="dynamic")

# 评论内容


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    topic_id = db.Column(db.Integer, db.ForeignKey("topic.id"))
    comment_time = db.Column(db.DateTime)

    replys = db.relationship("Reply", backref="Comment", lazy="dynamic")

# 评论回复


class Reply(db.Model):
    __tablename__ = 'reply'
    id = db.Column(db.Integer, primary_key=True)
    reply_content = db.Column(db.Text, nullable=False)
    reply_time = db.Column(db.DateTime)
    to_uid = db.Column(db.Integer)  # 回复对象

    from_uid = db.Column(db.Integer, db.ForeignKey("user.id"))  # 写这条回复的用户
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'))

# 小说


class Story(db.Model):
    __tablename__ = 'story'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    author = db.Column(db.String(30))
    type = db.Column(db.String(20))
    introduction = db.Column(db.Text)
    images = db.Column(db.String(255))

    StoryContents = db.relationship(
        "StoryContent", backref="Story", lazy="dynamic")
    storyHistorys = db.relationship(
        "StoryHistory", backref="story", lazy="dynamic")


# 小说每张内容
class StoryContent(db.Model):
    __tablename__ = 'storyContent'
    id = db.Column(db.Integer, primary_key=True)
    story_dir = db.Column(db.String(50))
    dir_flag = db.Column(db.Integer)
    content_path = db.Column(db.String(30))

    story_id = db.Column(db.Integer, db.ForeignKey("story.id"))


# 小说历史
class StoryHistory(db.Model):
    __tablename__ = 'storyHistory'
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(30))
    pub_date = db.Column(db.DateTime)

    story_id = db.Column(db.Integer, db.ForeignKey("story.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

# 点赞


class Voke(db.Model):
    __tablename__ = 'voke'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    topic_id = db.Column(db.Integer, db.ForeignKey("topic.id"))

# 图片类型


class ImageType(db.Model):
    __tablename__ = 'imageType'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20))
    images = db.relationship("Images", backref="ImageType", lazy="dynamic")

# 图片详情


class Images(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    describe = db.Column(db.String(100))
    imageSize = db.Column(db.String(20))
    imageUrl = db.Column(db.String(255))

    type_id = db.Column(db.Integer, db.ForeignKey("imageType.id"))
