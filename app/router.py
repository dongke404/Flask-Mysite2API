# 主业务逻辑中的视图和路由的定义
from . import app
from . import mongo
from flask import request, jsonify
# 导入实体类，用于操作数据库
from . import db
from app.config import REDISHOST, REDISPWD, REDISDB, REDISPORT, STORYBASEDIR, PICBASEDIR, JWTSECRET, DEFAULTAVATAR
from flask_cors import CORS
from .models import (User, Topic, TopicType, Comment, Reply, Story,
                     StoryContent, StoryHistory, ImageType, Voke, Follow)
import time
import jwt
import redis
import html2text
import re
import datetime

CORS(app, supports_credentials=True)

# 生产环境
baseurl = "/api"

# picBasedir = os.path.abspath(os.path.dirname(
# os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# 开发环境
# baseurl = ""
# picBasedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
# 验证身份函数


# 验证token函数
def cktoken(token):
    if not token:
        return jsonify({'status': -3, 'msg': "请登陆"})
    try:
        usertokenInfo = jwt.decode(token, JWTSECRET, algorithms=['HS256'])
        ctime = usertokenInfo.get("ctime")
        uid = usertokenInfo.get("id")
        expires = usertokenInfo.get("expires")
        # print("离身份过期的秒数:", int(expires) - int(time.time() - ctime))
        if int(time.time() - ctime) > int(expires):
            return jsonify({'status': -1, 'msg': "身份信息已过期"})
        else:
            return int(uid)
    except Exception as e:
        print(e)
        return jsonify({'status': -2, 'msg': "请重新登陆"})


# 发布前验证身份
@app.route(baseurl + '/ckuser', methods=["POST"])
def reqCkuser():
    params = request.get_json(silent=True)
    token = params.get("token")
    res = cktoken(token)
    if not isinstance(res, int):
        return res
    uid = res
    checkUser = db.session.query(User).filter(User.id == uid).first()
    data = {}
    data["voke_num"] = checkUser.voke_num
    data["topic_num"] = checkUser.topics.count()
    data["followed_num"] = db.session.query(Follow).filter(
        Follow.followed_id == checkUser.id).count()

    if checkUser:
        return jsonify({
            "status": 0,
            "data": data
        })
    else:
        return jsonify({"status": 1, "msg": "身份信息错误，请重新登陆"})


# 注册
@app.route(baseurl + '/reg', methods=["GET", "POST"])
def reg():
    # 动态用户名验证
    if request.method == "GET":
        loginname = request.args.get("loginname")
        # 检验重复
        checkRe = db.session.query(User).filter(
            (User.loginname == loginname)).first()
        if checkRe:
            return jsonify({"status": 1, "msg": "此用户已存在"})
        else:
            return jsonify({"status": 0, "msg": "用户名可用"})
    else:
        try:
            data = request.get_json(silent=True)
            loginname = data.get("loginname")
            password = data.get("password")
            email = data.get("email")
            nickname = data.get("nickname")
            checkRename = db.session.query(User).filter(
                (User.loginname == loginname)).first()
            checkReemail = db.session.query(User).filter(
                (User.email == email)).first()
            if checkRename or checkReemail:
                return jsonify({"status": 1, "msg": "邮箱地址已存在"})
            else:
                userinfo = User()
                userinfo.loginname = loginname
                userinfo.password = password
                userinfo.email = email
                userinfo.nickname = nickname
                userinfo.head_link = DEFAULTAVATAR
                db.session.add(userinfo)
                Userinfo = db.session.query(User).filter(
                    User.loginname == loginname).first()
                id = Userinfo.id
                db.session.commit()
                token = jwt.encode(
                    {
                        "id": id,
                        "ctime": int(time.time()),
                        'expires': 60 * 60 * 24 * 7
                    },
                    JWTSECRET,
                    algorithm='HS256')
                return jsonify({
                    "status": 0,
                    "data": {
                        "nickname": nickname,
                        "email": email,
                        "head_link": DEFAULTAVATAR,
                        "token": token.decode()
                    }
                })
        except Exception as e:
            print(e)
            return jsonify({"status": 1, "msg": "未知错误"})


# 登录验证
@app.route(baseurl + '/login', methods=["POST"])
def login():
    data = request.get_json(silent=True)
    loginname = data.get("loginname")
    password = data.get("password")
    checkUser = db.session.query(User).filter(
        User.loginname == loginname, User.password == password).first()
    if checkUser:
        id = checkUser.id
        email = checkUser.email
        nickname = checkUser.nickname
        head_link = checkUser.head_link
        introduction = checkUser.introduction
        music_like = checkUser.music_like.split(
            ",") if checkUser.music_like else ""
        clt_topic = checkUser.clt_topic.split(
            ",") if checkUser.clt_topic else ""

        # 找出我关注的
        myfollows = []
        follows = db.session.query(Follow).filter(Follow.follow_id == id).all()
        for obj in follows:
            myfollows.append(obj.followed_id)
        token = jwt.encode(
            {
                "id": id,
                "ctime": int(time.time()),
                'expires': 60 * 60 * 24 * 7
            },
            JWTSECRET,
            algorithm='HS256')
        return jsonify({
            "status": 0,
            "data": {
                "id": id,
                "nickname": nickname,
                "email": email,
                "head_link": head_link,
                "music_like": music_like,
                "clt_topic": clt_topic,
                "introduction": introduction,
                "token": token.decode()
            },
            "myfollows": myfollows
        })
    else:
        return jsonify({"status": 1, "msg": "用户名密码错误"})

# 用户基本信息获取
@app.route(baseurl + '/userbasicinfo')
def userbasicinfo():
    params = request.args
    uid = params.get("uid")

    try:
        data = {}
        user = db.session.query(User).filter(User.id == uid).first()
        data["nickname"] = user.nickname
        data["head_link"] = user.head_link
        data["introduction"] = user.introduction
        data["email"] = user.email
        return jsonify({"status": 0, "data": data})
    except Exception as e:
        print(e)
        return jsonify({"status": 1, "data": data, "msg": "请求失败"})


# 信息修改
@app.route(baseurl + '/modifyUser', methods=["POST"])
def modifyUser():
    data = request.get_json(silent=True)
    token = data.get("token")
    res = cktoken(token)
    try:
        if not isinstance(res, int):
            return res
        user_id = res
        flag = data.get("type")
        value = data.get("value")
        if flag == "nickname":
            user = db.session.query(User).filter(User.id == user_id).first()
            user.nickname = value
            db.session.commit()
            return jsonify({"status": 0, "data": value, "msg": "修改成功"})
        if flag == "email":
            user = db.session.query(User).filter(User.id == user_id).first()
            checkReemail = db.session.query(User).filter(
                User.id != user_id, User.email == value).first()
            print(checkReemail)
            if checkReemail:
                return jsonify({"status": 2, "msg": "邮箱地址已存在"})
            user.email = value
            db.session.commit()
            return jsonify({"status": 0, "data": value, "msg": "修改成功"})
        if flag == "introduction":
            user = db.session.query(User).filter(User.id == user_id).first()
            user.introduction = value
            db.session.commit()
            return jsonify({"status": 0, "data": value, "msg": "修改成功"})
    except Exception as e:
        print(e)
        return jsonify({"status": 1, "data": value, "msg": "操作失败"})


# 获取我收藏的帖子
@app.route(baseurl + '/cltTopic', methods=["POST"])
def cltTopic():
    params = request.get_json(silent=True)
    token = params.get("token")
    res = cktoken(token)
    if not isinstance(res, int):
        return res
    user_id = res
    try:
        user = db.session.query(User).filter(User.id == user_id).first()
        clt_topic = user.clt_topic.split(",")
        topics = []
        for topicid in clt_topic:
            info = {}
            topicObj = db.session.query(Topic).filter(
                Topic.id == topicid).first()
            replyObj = db.session.query(Reply).filter(
                Reply.topic_id == topicid).order_by(Reply.id.desc()).first()
            if topicObj:
                info["key"] = topicObj.id
                info["title"] = topicObj.title[0:20]
                info["author"] = topicObj.user.nickname
                if replyObj:
                    info["time"] = replyObj.reply_time.strftime(
                        "%Y-%m-%d %H:%M:%S")

                topics.append(info)
        return jsonify({"status": 0, "data": topics, "msg": "修改成功"})
    except Exception as e:
        print(e)
        return jsonify({"status": 1, "msg": "请求失败"})


# 获取我发布的帖子 或者 用户发布的贴子
@app.route(baseurl + '/myTopics', methods=["GET", "POST"])
def myTopics():
    if request.method == "GET":
        params = request.args
        user_id = params.get("id")
    else:
        params = request.get_json(silent=True)
        token = params.get("token")
        res = cktoken(token)
        if not isinstance(res, int):
            return res
        user_id = res
    try:
        topics = db.session.query(Topic).filter(
            Topic.user_id == user_id).order_by(Topic.id.desc()).all()
        data = []
        for topicObj in topics:
            replyObj = db.session.query(Reply).filter(
                Reply.topic_id == topicObj.id).order_by(Reply.id.desc()).first()
            _ = {}
            _["key"] = topicObj.id
            _["title"] = topicObj.title[0:20]
            _["pubtime"] = topicObj.pub_date.strftime("%Y-%m-%d %H:%M")
            if replyObj:
                _["time"] = replyObj.reply_time.strftime("%Y-%m-%d %H:%M")
            data.append(_)
        return jsonify({"status": 0, "data": data})
    except Exception as e:
        print(e)
        return jsonify({"status": 1, "msg": "请求失败"})


# 获取我参与的帖子
@app.route(baseurl + '/myRepCmt', methods=["POST"])
def myRepCmt():
    params = request.get_json(silent=True)
    token = params.get("token")
    res = cktoken(token)
    if not isinstance(res, int):
        return res
    user_id = res
    try:
        # 我评论的
        comments = db.session.query(Comment).filter(
            Comment.user_id == user_id).all()
        mycmts = []
        for comment in comments:
            cObj = {}
            if comment.topic_id:
                cObj["flag"] = 1
                cObj["topic"] = comment.topic.title
                cObj["topic_id"] = comment.topic_id
                cObj["to_uid"] = comment.topic.user_id
                cObj["to_uname"] = comment.topic.user.nickname
                cObj["text"] = comment.comment
                cObj["time"] = comment.comment_time.strftime("%Y%m%d%H%M%S")
                mycmts.append(cObj)
        # 我回复的
        replys = db.session.query(Reply).filter(
            Reply.from_uid == user_id).all()
        myreps = []
        for reply in replys:
            rObj = {}
            topicObj = db.session.query(Topic).filter(
                Topic.id == reply.topic_id).first()
            if topicObj:
                rObj["flag"] = 2
                rObj["topic"] = topicObj.title
                rObj["topic_id"] = topicObj.id
                rObj["to_uid"] = reply.to_uid
                userObj = db.session.query(User).filter(
                    User.id == reply.to_uid).first()
                rObj["to_uname"] = userObj.nickname
                rObj["text"] = reply.reply_content
                rObj["time"] = reply.reply_time.strftime("%Y%m%d%H%M%S")
                myreps.append(rObj)
        # 回复我的
        tomeReplys = db.session.query(Reply).filter(
            Reply.to_uid == user_id).all()
        print(tomeReplys)
        tomereps = []
        for tomerep in tomeReplys:
            tObj = {}
            topicObj = db.session.query(Topic).filter(
                Topic.id == tomerep.topic_id).first()
            if topicObj:
                tObj["flag"] = 3
                tObj["topic"] = topicObj.title
                tObj["topic_id"] = topicObj.id
                tObj["to_uid"] = reply.from_uid
                tObj["to_uname"] = reply.user.nickname
                tObj["text"] = reply.reply_content
                tObj["time"] = reply.reply_time.strftime("%Y%m%d%H%M%S")
                tomereps.append(tObj)
        data = mycmts+myreps+tomereps
        return jsonify({"status": 0, "data": data})
    except Exception as e:
        print(e)
        return jsonify({"status": 1, "msg": "请求失败"})


# 删除我发布的帖子
@app.route(baseurl + '/delTopics', methods=["POST"])
def delTopics():
    params = request.get_json(silent=True)
    token = params.get("token")
    res = cktoken(token)
    if not isinstance(res, int):
        return res
    user_id = res
    topicid = params.get("topicid")
    try:
        topic = db.session.query(Topic).filter(
            Topic.id == topicid, Topic.user_id == user_id).first()
        db.session.delete(topic)
        return jsonify({"status": 0,  "msg": "删除成功"})
    except Exception as e:
        print(e)
        return jsonify({"status": 1, "msg": "请求失败"})

# 获取关注的人或被关注(1:关注 2，被关注)
@app.route(baseurl + '/followUser', methods=["GET", "POST"])
def followUser():
    if request.method == "GET":
        params = request.args
        user_id = params.get("uid")
    else:
        params = request.get_json(silent=True)
        token = params.get("token")
        res = cktoken(token)
        if not isinstance(res, int):
            return res
        user_id = res
    flag = params.get("flag")
    try:
        if flag == "1":
            follows = db.session.query(Follow).filter(
                Follow.follow_id == user_id).all()
        if flag == "2":
            follows = db.session.query(Follow).filter(
                Follow.followed_id == user_id).all()
        data = []
        for _ in follows:
            user = {}
            if flag == "1":
                uid = _.followed_id
            if flag == "2":
                uid = _.follow_id
            targetUser = db.session.query(User).filter(User.id == uid).first()
            print(targetUser)
            user["id"] = uid
            user["head_link"] = targetUser.head_link
            user["nickname"] = targetUser.nickname
            user["voke_num"] = targetUser.voke_num
            user["introduction"] = targetUser.introduction
            ufollows = db.session.query(Follow).filter(
                Follow.follow_id == uid).count()
            user["follow"] = ufollows
            ufolloweds = db.session.query(Follow).filter(
                Follow.followed_id == uid).count()
            user["followed"] = ufolloweds
            data.append(user)
        return jsonify({"status": 0, "data": data})
    except Exception as e:
        print(e)
        return jsonify({"status": 1, "msg": "请求失败"})


# 帖子上传
@app.route(baseurl + '/uploadtopic', methods=["POST"])
def uploadtopic():
    try:
        data = request.get_json(silent=True)
        token = data.get("token")
        res = cktoken(token)
        if not isinstance(res, int):
            return res
        user_id = res
        type_id = data.get("type_id")
        title = data.get("title")
        content = data.get("content")
        # 正则取图片链接
        regex = re.compile(r'<img src="(.*?)"', re.S)
        img_list = regex.findall(content)
        topic = Topic()
        topic.user_id = user_id
        topic.type_id = type_id
        topic.title = title
        topic.pub_date = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        topic.content = content
        topic.images = str(img_list)
        topic.read_num = 0
        db.session.add(topic)
        db.session.commit()
        return jsonify({
            "status": 0,
        })

    except Exception as e:
        print(e)
        return jsonify({
            "status": 1,
        })


# 主页帖子内容
@app.route(baseurl + '/reqtopic')
def reqtopic():
    data = request.args
    page = int(data.get("page"))  # 传送第页内容
    pageNum = int(data.get("pageNum"))  # 每页显示的数量
    typeId = data.get("typeId")
    tag = data.get("tag")
    onePageNum = ((page - 1) * pageNum, page * pageNum)
    # 有类型
    if typeId != "0":
        total = db.session.query(Topic).filter(
            (Topic.type_id == typeId)).count()
        if tag == "newest":
            topics = db.session.query(Topic) \
                .filter((Topic.type_id == typeId)) \
                .order_by(Topic.id.desc()) \
                .slice(*onePageNum) \
                .all()  # 按最新排序
        else:
            topics = db.session.query(Topic) \
                .filter((Topic.type_id == typeId)) \
                .order_by(Topic.read_num.desc()) \
                .slice(*onePageNum) \
                .all()  # 按最热排序
    else:
        total = db.session.query(Topic).count()
        if tag == "newest":
            topics = db.session.query(Topic).order_by(
                Topic.id.desc()).slice(*onePageNum).all()  # 按最新排序
        else:
            topics = db.session.query(Topic).order_by(
                Topic.read_num.desc()).slice(*onePageNum).all()  # 按最热排序

    # 提取文本
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    data = []
    for topic in topics:
        obj = {}
        obj["id"] = topic.id
        obj["title"] = topic.title[:30]  # 限制显示字数
        obj["read_num"] = topic.read_num
        content = h.handle(topic.content)[:100]  # 限制显示字数
        obj["content"] = content
        obj["pub_date"] = str(topic.pub_date)
        # user信息
        obj["user"] = {}
        obj["user"]["id"] = topic.user.id
        obj["user"]["nickname"] = topic.user.nickname
        obj["user"]["head_link"] = topic.user.head_link
        obj["user"]["email"] = topic.user.email
        images = eval(topic.images)
        obj["images"] = images
        # 评论数
        comments = db.session.query(Comment).filter(
            Comment.topic_id == topic.id).all()
        commentTotal = 0
        replysTotal = 0
        for comment in comments:
            commentTotal += 1
            replys = db.session.query(Reply).filter(
                Reply.comment_id == comment.id).all()
            replysNum = len(replys)
            replysTotal += replysNum
        obj["replytotal"] = commentTotal + replysTotal
        data.append(obj)

    return jsonify({
        "status": 0,
        "total": int(total),
        "data": data,
    })


# 获取分类列表
@app.route(baseurl + '/topicTypes')
def reqTopicTypes():
    typeList = db.session.query(TopicType).all()
    data = []
    for typeobj in typeList:
        imagetype = {}
        imagetype["id"] = typeobj.id
        imagetype["type"] = typeobj.type
        data.append(imagetype)
    return jsonify({'status': 0, 'data': data})


# 帖子详细内容
@app.route(baseurl + '/reqpostdetail')
def reqPostDetail():
    try:
        topicId = request.args.get("id")
        topic = db.session.query(Topic).filter(Topic.id == topicId).first()
        # 浏览量+1
        topic.read_num += 1
        theme = {}
        theme["title"] = topic.title
        theme["type"] = topic.topicType.type
        theme["content"] = topic.content
        theme["pub_date"] = str(topic.pub_date)
        theme["user"] = topic.user.nickname
        theme["uid"] = topic.user.id
        theme["head_link"] = topic.user.head_link
        theme["read_num"] = topic.read_num
        theme["user_voke"] = topic.user.voke_num
        theme["user_topicNum"] = topic.user.topics.count()
        theme["user_followed"] = db.session.query(Follow).filter(
            Follow.followed_id == topic.user.id).count()
        # 获取评论
        commentlist = db.session.query(Comment).filter(
            Comment.topic_id == topicId).all()
        comments = []
        for commentobj in commentlist:
            comment = {}
            comment["id"] = commentobj.id
            comment["comment"] = commentobj.comment
            comment["date"] = str(commentobj.comment_time)
            vokes = commentobj.vokes.all()
            vokeIds = []
            for voke in vokes:
                vokeIds.append(voke.user_id)
            comment['vokeIds'] = vokeIds
            # 评论里添加用户信息
            userobj = commentobj.user
            comment["user"] = {}
            user = comment["user"]
            user["id"] = userobj.id
            user["nickname"] = userobj.nickname
            user["head_link"] = userobj.head_link
            comments.append(comment)
            # 评论里添加回复信息
            replysobjList = commentobj.replys.all()
            comment["replys"] = []
            replyList = comment["replys"]
            for replyobj in replysobjList:
                reply = {}
                reply["id"] = replyobj.id
                reply["author"] = replyobj.user.nickname
                reply["author_id"] = replyobj.user.id
                reply["authorHead"] = replyobj.user.head_link
                reply["to_id"] = replyobj.to_uid
                toUserobj = db.session.query(User).filter(
                    User.id == replyobj.to_uid).first()
                reply["to_nickname"] = toUserobj.nickname
                reply["reply_content"] = replyobj.reply_content
                reply["datetime"] = str(replyobj.reply_time)
                replyList.append(reply)
        return jsonify({"status": 0, "theme": theme, "comments": comments})
    except Exception as e:
        print(e)
        return jsonify({"status": 1, "msg": "未知错误"})


# 收藏帖子
@app.route(baseurl + '/reqCollect', methods=["POST"])
def collectTopic():
    try:
        data = request.get_json(silent=True)
        token = data.get("token")
        res = cktoken(token)
        if not isinstance(res, int):
            return res
        uid = res
        topicId = str(data.get("topicId"))
        user = db.session.query(User).filter(User.id == uid).first()
        topics = user.clt_topic
        if not topics:
            user.clt_topic = topicId
            topicList = topicId.split(",")
        else:
            topicList = topics.split(",")
            if topicId in topicList:
                topicList.remove(topicId)
            else:
                topicList.append(topicId)
            _ = ""
            for i in topicList:
                _ += i + ","
            user.clt_topic = _[0:-1]
        resLst = topicList
        db.session.add(user)
        db.session.commit()
        return jsonify({'status': 0, "data": resLst})
    except Exception as e:
        print(e)
        return jsonify({'status': 1, 'msg': '操作失败'})


# 点赞评论
@app.route(baseurl + '/reqZan', methods=["POST"])
def clickZan():
    try:
        data = request.get_json(silent=True)
        token = data.get("token")
        res = cktoken(token)
        if not isinstance(res, int):
            return res
        uid = res
        comment_id = data.get("comment_id")
        voke = db.session.query(Voke).filter(
            Voke.user_id == uid, Voke.comment_id == comment_id).first()
        comment = db.session.query(Comment).filter(
            Comment.id == comment_id).first()
        user = comment.user
        if voke:
            db.session.delete(voke)
            user.voke_num = int(user.voke_num) - 1
        else:
            voke = Voke()
            voke.comment_id = comment_id
            voke.user_id = uid
            db.session.add(voke)
            user.voke_num = int(user.voke_num) + 1
        db.session.commit()
        return jsonify({'status': 0})
    except Exception as e:
        print(e)
        return jsonify({'status': 1, 'msg': '操作失败'})


# 点击关注
@app.route(baseurl + '/reqFollow', methods=["POST"])
def reqFollow():
    try:
        data = request.get_json(silent=True)
        token = data.get("token")
        res = cktoken(token)
        if not isinstance(res, int):
            return res
        uid = res
        followed_uid = data.get("followed_uid")
        if uid == int(followed_uid):
            return jsonify({'status': 2, 'msg': '无法关注自己'})
        follow = db.session.query(Follow).filter(
            Follow.follow_id == uid,
            Follow.followed_id == followed_uid).first()
        if follow:
            db.session.delete(follow)
        else:
            follow = Follow()
            follow.followed_id = followed_uid
            follow.follow_id = uid
            db.session.add(follow)
        db.session.commit()
        myfollows = []
        follows = db.session.query(Follow).filter(
            Follow.follow_id == uid).all()
        for obj in follows:
            myfollows.append(obj.followed_id)
        return jsonify({'status': 0, 'data': myfollows})
    except Exception as e:
        print(e)
        return jsonify({'status': 1, 'msg': '操作失败'})

# 移除粉丝(关注)
@app.route(baseurl + '/rmFollow', methods=["POST"])
def rmFollow():
    try:
        data = request.get_json(silent=True)
        token = data.get("token")
        res = cktoken(token)
        if not isinstance(res, int):
            return res
        uid = res
        rmid = data.get("rmid")
        follow = db.session.query(Follow).filter(
            Follow.follow_id == rmid,
            Follow.followed_id == uid).first()
        if follow:
            db.session.delete(follow)
        db.session.commit()
        return jsonify({'status': 0})
    except Exception as e:
        print(e)
        return jsonify({'status': 1, 'msg': '操作失败'})


# 图片上传
@app.route(baseurl + '/img/upload', methods=["POST"])
def imgupload():
    img = request.files['upfile']
    path = PICBASEDIR + '/static/images/uploadImg/'
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f") + \
        (img.filename[-8:])  # 图片防止重复
    file_path = path + filename
    img.save(file_path)
    # 返回预览图
    return jsonify({
        'errno': 0,
        'data': ['/static/images/uploadImg/' + filename]
    })


# 头像上传
@app.route(baseurl + '/uploadhead', methods=["POST"])
def uploadhead():
    token = request.form["token"]
    res = cktoken(token)
    if not isinstance(res, int):
        return res
    try:
        id = res
        img = request.files["avatar"]
        savepath = PICBASEDIR + '/static/images/uploadHead/'
        imgname = img.filename
        img.save(savepath + imgname)
        user = db.session.query(User).filter(User.id == id).first()
        getimgpath = '/static/images/uploadHead/' + imgname
        user.head_link = getimgpath
        return jsonify({'status': 0, 'avatarPath': getimgpath})
    except Exception as e:
        print(e)
        return jsonify({'status': 1, 'msg': "请求失败"})


# 添加喜欢的音乐
@app.route(baseurl + '/addmusicLike', methods=["POST"])
def addmusicLike():
    try:
        data = request.get_json(silent=True)
        token = data.get("token")
        res = cktoken(token)
        if not isinstance(res, int):
            return res
        uid = res
        musicid = data.get("musicId")
        user = db.session.query(User).filter(User.id == uid).first()
        musics = user.music_like
        if not musics:
            user.music_like = musicid
            musicList = musicid.split(",")
        else:
            musicList = musics.split(",")
            if musicid in musicList:
                musicList.remove(musicid)
            else:
                musicList.append(musicid)
            _ = ""
            for i in musicList:
                _ += i + ","
            user.music_like = _[0:-1]
        resLst = musicList
        db.session.add(user)
        db.session.commit()
        return jsonify({'status': 0, "data": resLst})
    except Exception as e:
        print(e)
        return jsonify({'status': 1, 'msg': '操作失败'})


# 评论存储
@app.route(baseurl + '/upComment', methods=["POST"])
def upComment():
    params = request.get_json(silent=True)
    token = params.get('token')
    res = cktoken(token)
    if not isinstance(res, int):
        return res
    user_id = res
    topic_id = params.get("topic_id")
    comment = params.get("comment")
    try:
        commentobj = Comment()
        commentobj.user_id = user_id
        commentobj.topic_id = topic_id
        commentobj.comment = comment
        commentobj.comment_time = datetime.datetime.now().strftime(
            "%Y%m%d%H%M%S")
        db.session.add(commentobj)
        db.session.commit()
        return jsonify({'status': 0})
    except Exception as e:
        print(e)
        return jsonify({'status': 1, "msg": "提交失败"})


# 回复处理
@app.route(baseurl + '/pbReply', methods=["POST"])
def pbReply():
    params = request.get_json(silent=True)
    token = params.get("token")
    res = cktoken(token)
    if not isinstance(res, int):
        return res
    from_uid = res
    to_uid = params.get("to_uid")
    if int(from_uid) == int(to_uid):
        return jsonify({'status': 2, "msg": "请不要回复自己"})
    comment_id = params.get("comment_id")
    reply_content = params.get("reply_content")
    try:
        commentObj = db.session.query(Comment).filter(
            Comment.id == comment_id).first()
        replyObj = Reply()
        replyObj.from_uid = from_uid
        replyObj.to_uid = to_uid
        replyObj.comment_id = comment_id
        replyObj.reply_content = reply_content
        replyObj.reply_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        replyObj.topic_id = commentObj.topic_id
        db.session.add(replyObj)
        db.session.commit()
        return jsonify({'status': 0})
    except Exception as e:
        print(e)
        return jsonify({'status': 1, "msg": "提交失败"})


# 获取头像
@app.route(baseurl + '/reqhead')
def reqhead():
    try:
        id = request.args.get("id")
        user = db.session.query(User).filter(User.id == id).first()
        id = user.id
        loginname = user.loginname
        email = user.email
        nickname = user.nickname
        head_link = user.head_link
        return jsonify({
            "status": 0,
            "data": {
                "id": id,
                "loginname": loginname,
                "nickname": nickname,
                "email": email,
                "head_link": head_link
            }
        })
    except Exception as e:
        print(e)
        return jsonify({'status': 1, 'msg': "更新头像失败"})


# 获取新闻内容
@app.route(baseurl + '/reqNews')
def reqNews():
    r = redis.StrictRedis(host=REDISHOST,
                          port=REDISPORT,
                          db=REDISDB,
                          password=REDISPWD)
    data = {}
    # 优化 可封装函数
    # 获取横幅消息
    data["banner"] = []
    for key in r.keys("banner*"):
        banner = {}
        for i, name in enumerate(["title", "imgUrl", "newsUrl"]):
            value = r.lindex(key, i)
            banner[name] = value.decode()
        data["banner"].append(banner)
    # 获取侧边栏信息
    data["sideimg"] = []
    for key1 in r.keys("sideimg*"):
        sideimg = {}
        for i, name in enumerate(['sidetitle', 'sideImgUrl', 'sideUrl']):
            value = r.lindex(key1, i)
            sideimg[name] = value.decode()
        data["sideimg"].append(sideimg)
    # 获取热点信息
    data["hotevent"] = []
    for key2 in sorted(r.keys("Hotevent*"),
                       key=lambda x: int(x.decode().split('Hotevent')[1])):
        hotevent = {}
        for i, name in enumerate(['title', 'link']):  # 0 :title 1 imgUrl 2 url
            value = r.lindex(key2, i)
            hotevent[name] = value.decode()
        data["hotevent"].append(hotevent)
    return jsonify({
        'status': 0,
        "data": data,
    })


# 获取小说列表
@app.route(baseurl + '/story')
def reqStory():
    params = request.args
    stype = params.get("stype")
    if stype == "全部小说" or (not stype):
        bookList = db.session.query(Story).all()
    else:
        bookList = db.session.query(Story).filter(Story.type == stype).all()
    data = []
    for bookobj in bookList:
        book = {}
        book["id"] = bookobj.id
        book["name"] = bookobj.name
        book["author"] = bookobj.author
        book["type"] = bookobj.type
        book["introduction"] = bookobj.introduction[0:50]
        book["images"] = bookobj.images
        data.append(book)
    return jsonify({
        'status': 0,
        "data": data,
    })

# 搜索小说
@app.route(baseurl + '/searchBook')
def reqSearchBook():
    params = request.args
    name = params.get("name")
    bookList = db.session.query(Story).filter(
        Story.name.like("%" + name + "%") if name is not None else ""
    ).all()
    data = []
    for bookobj in bookList:
        book = {}
        book["id"] = bookobj.id
        book["name"] = bookobj.name
        book["author"] = bookobj.author
        book["type"] = bookobj.type
        book["introduction"] = bookobj.introduction[0:50]
        book["images"] = bookobj.images
        data.append(book)
    return jsonify({
        'status': 0,
        "data": data,
    })


# 获取小说类型
@app.route(baseurl + '/storyTypeList')
def reqStoryTypeList():
    typelist = db.session.query(Story.type).distinct().all()
    data = []
    for i in typelist:
        data.append(i[0])
    return jsonify({'status': 0, "data": data})


# 获取小说目录
@app.route(baseurl + '/storydirs')
def reqStoryDirs():
    params = request.args
    id = params.get("storyid")
    storyobj = db.session.query(Story).filter(Story.id == id).first()
    data = {}
    data["id"] = storyobj.id
    data["name"] = storyobj.name
    data["author"] = storyobj.author
    data["type"] = storyobj.type
    data["introduction"] = storyobj.introduction
    storyContents = storyobj.StoryContents.all()
    dirs = []
    for storyContent in storyContents:
        _ = {}
        _["id"] = storyContent.id
        _["dir"] = storyContent.story_dir
        _["path"] = storyContent.content_path
        dirs.append(_)
    data["dirs"] = dirs
    return jsonify({'status': 0, "data": data})


# 获取小说内容
@app.route(baseurl + '/storyContent', methods=["POST"])
def reqStoryContent():
    data = request.get_json(silent=True)
    token = data.get("token")
    story_id = data.get("storyid")
    path = data.get("path")
    try:
        if token:
            res = cktoken(token)
            if not isinstance(res, int):
                return res
            uid = res
            historyObj = db.session.query(StoryHistory).filter(
                StoryHistory.story_id == story_id,
                StoryHistory.user_id == uid).first()
            if historyObj:
                db.session.delete(historyObj)
            newHistory = StoryHistory(path=path,
                                      pub_date=datetime.datetime.now(),
                                      story_id=story_id,
                                      user_id=uid)
            db.session.add(newHistory)
            db.session.commit()

        storyContentobj = db.session.query(StoryContent).filter(
            StoryContent.content_path == path,
            StoryContent.story_id == story_id).first()
        storytext = storyContentobj.dir_flag
        storyobj = storyContentobj.Story
        with open(STORYBASEDIR +
                  "/storys/{}/{}.txt".format(storyobj.name, storytext),
                  encoding="utf-8") as f:
            text = f.read()
        data = {}
        data["type"] = storyobj.type
        data["dir"] = storyContentobj.story_dir
        data["name"] = storyobj.name
        data["storyid"] = storyobj.id
        data["text"] = text
        return jsonify({'status': 0, "data": data})
    except Exception as e:
        print(e)
        return jsonify({'status': 1, "msg": "请求失败"})


# 获取下一页
@app.route(baseurl + '/storyNextPage', methods=["POST"])
def reqStoryNextPage():
    params = request.get_json(silent=True)
    token = params.get("token")
    story_id = params.get("storyid")
    path = params.get("path")
    try:
        storyContentobj = db.session.query(StoryContent).filter(
            StoryContent.content_path == path,
            StoryContent.story_id == story_id).first()
        nextdir_flag = storyContentobj.dir_flag + 1
        nextstoryContentobj = db.session.query(StoryContent).filter(
            StoryContent.dir_flag == nextdir_flag,
            StoryContent.story_id == story_id).first()
        path = nextstoryContentobj.content_path
        if token:
            res = cktoken(token)
            if not isinstance(res, int):
                return res
            uid = res
            historyObj = db.session.query(StoryHistory).filter(
                StoryHistory.story_id == story_id,
                StoryHistory.user_id == uid).all()
            if historyObj:
                for obj in historyObj:
                    db.session.delete(obj)
            newHistory = StoryHistory(path=path,
                                      pub_date=datetime.datetime.now(),
                                      story_id=story_id,
                                      user_id=uid)
            db.session.add(newHistory)
            db.session.commit()
        if not nextstoryContentobj:
            return jsonify({'status': 1, "msg": "没有更多了"})
        storytext = nextstoryContentobj.dir_flag
        storyobj = nextstoryContentobj.Story
        with open(STORYBASEDIR +
                  "/storys/{}/{}.txt".format(storyobj.name, storytext),
                  encoding="utf-8") as f:
            text = f.read()
        data = {}
        data["type"] = storyobj.type
        data["dir"] = nextstoryContentobj.story_dir
        data["name"] = storyobj.name
        data["storyid"] = storyobj.id
        data["text"] = text
        data["path"] = path
        return jsonify({'status': 0, "data": data})
    except Exception as e:
        print(e)
        return jsonify({'status': 1, "msg": "请求失败"})


# 获取历史记录
@app.route(baseurl + '/storyHistory', methods=["POST"])
def reqstoryHistory():
    try:
        params = request.get_json(silent=True)
        token = params.get("token")
        flag = params.get("flag")
        res = cktoken(token)
        if not isinstance(res, int):
            return res
        uid = res
        historyList = db.session.query(StoryHistory).filter(
            StoryHistory.user_id == uid).order_by(
                StoryHistory.id.desc()).all()
        data = []
        for obj in historyList:
            _ = {}
            _["name"] = obj.story.name
            storycontent = db.session.query(StoryContent).filter(
                StoryContent.content_path == obj.path).first()
            _["dir"] = storycontent.story_dir
            _["storyid"] = obj.story_id
            _["path"] = obj.path
            data.append(_)
        if flag:
            data = data
        else:
            data = data[0:10]
        return jsonify({'status': 0, "data": data})
    except Exception as e:
        print(e)
        return jsonify({'status': 1, "msg": "请求失败"})


# 获取分类列表
@app.route(baseurl + '/imagesTypes')
def reqImagesTypes():
    typeList = db.session.query(ImageType).all()
    data = []
    for typeobj in typeList:
        imagetype = {}
        imagetype["id"] = typeobj.id
        imagetype["type"] = typeobj.type
        data.append(imagetype)
    return jsonify({'status': 0, 'data': data})


# 获取图片内容
@app.route(baseurl + '/imagesInfo')
def reqImagesInfo():
    params = request.args
    type_id = params.get("typeId")
    curPage = params.get("curPage")
    typeobj = db.session.query(ImageType).filter(
        ImageType.id == type_id).first()
    images = typeobj.images.limit(50).offset((int(curPage) - 1) * 50).all()
    if images:
        data = []
        for imageobj in images:
            image = {}
            image["id"] = imageobj.id
            image["describe"] = imageobj.describe
            image["imageSize"] = imageobj.imageSize
            image["imageUrl"] = imageobj.imageUrl
            data.append(image)
        return jsonify({'status': 0, 'data': data})
    return jsonify({'status': 1, 'msg': "已经没有更多了"})


# 获取电影内容
@app.route(baseurl + '/reqMovies')
def reqMovies():
    set = mongo.db.movieInfo
    data = []
    for x in set.find({}, {
            "_id": 0,
            "introduce": 1,
            'subject.id': 1,
            'subject.actors': 1,
            'subject.rate': 1,
            'subject.duration': 1,
            'subject.types': 1,
            'subject.title': 1,
            'subject.region': 1,
            'subject.short_comment.content': 1
    }):
        name = x["subject"]["title"]
        name = name.split()[0]
        x["name"] = name
        data.append(x)
    return jsonify({'status': 0, 'data': data})
