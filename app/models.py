from . import db, login_manager
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app, request
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
import hashlib

# # database initialization: 
# Role.insert_roles()
# User.generate_fake()
# Post.generate_fake()

class Permission:
    """Flags for for roles permissions"""
    FOLLOW = 0X01
    COMMENT = 0X02
    WRITE_ARTICLES = 0X04
    MODERATE_COMMENTS = 0X08
    ADMINISTER = 0X80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '|Role {}|'.format(self.name)

    @staticmethod
    def insert_roles():
        roles = {
        'User': (Permission.FOLLOW | 
            Permission.COMMENT | 
            Permission.WRITE_ARTICLES, True),

        'Moderator': (Permission.FOLLOW | 
            Permission.COMMENT | 
            Permission.WRITE_ARTICLES | 
            Permission.MODERATE_COMMENTS, False),

        'Administrator': (0xff, False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

# order of definition of association table?
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    avatar_hash = db.Column(db.String(32))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    # this user follows 
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id], 
        backref=db.backref('follower', lazy=True), lazy='dynamic', 
        cascade='all, delete-orphan')
    # this user is followed by
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id], 
        backref=db.backref('followed', lazy='joined'), lazy='dynamic', 
        cascade='all, delete-orphan')


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.follow(self)
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash_maker()
        if self.role is None:
            if self.email == current_app.config['SONGBOOK_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            else:
                self.role = Role.query.filter_by(default=True).first()

        # super(User, self).__init__(**kwargs)
        # if self.role is None:
        #     if self.email == current_app.config['FLASKY_ADMIN']:
        #         self.role = Role.query.filter_by(permissions=0xff).first()
        #     if self.role is None:
        #         self.role = Role.query.filter_by(default=True).first()
        # if self.email is not None and self.avatar_hash is None:
        #     self.avatar_hash = hashlib.md5(
        #         self.email.encode('utf-8')).hexdigest()

    # update default to more attractive site based one :)
    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            #why can't site just specify https url?
            url = 'https://www.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'

        if self.avatar_hash is None:
            avatar_hash_maker()

        return '{url}/{avatar_hash}?s={size}&d={default}&r={rating}'.format(
            url=url, avatar_hash=self.avatar_hash, size=size, default=default, rating=rating)

    def avatar_hash_maker(self):
        encoded_email = self.email.lower().encode('utf-8')
        self.avatar_hash = hashlib.md5(encoded_email).hexdigest()

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({ 'confirm': self.id })


    def generate_password_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({ 'password_reset': self.id })


    def password_reset_confirm(self, token, password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        #Don't make users confirm and reset password separately.
        self.confirmed = True
        self.password(password)
        return True

    def __repr__(self):
        return '{}, {}'.format(self.name, self.role)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and (
            # bitwise and between assigned and requested permissions
            (self.role.permissions & permissions) == permissions)

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    # called each time a user request is received in auth/views
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        # followed = follower_id
        f = self.followed.filter_by(followed_id=user_id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Post.author_id == Follow.followed_id).filter(self.id == Follow.follower_id)

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py
        import sys

        seed()
        for i in range(count):
            username = forgery_py.name.first_name()
            u = User(email=forgery_py.internet.email_address(username),
                     username=username,
                     password='test',
                     name=username + " " + forgery_py.name.last_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentences(4),
                     member_since=forgery_py.date.date(past=True),
                     confirmed=True
                     )
            db.session.add(u)
            try:
                db.session.commit()
            # exception for non-unique data (not enough names in random generator)
            except IntegrityError:
                print(sys.exc_info()[0])
                db.session.rollback()


# no db.Model inheritance since nothing gets stored!
class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

# callable for custom anonymous_user requirements
login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    body = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1,4)), 
                     timestamp=forgery_py.date.date(True), author=u)
            db.session.add(p)
            db.session.commit()



