import twitter
import sqlalchemy as sql
import sqlalchemy.ext.declarative as sql_decl
import datetime
import os, errno
import sys


def main():
    sess = open_session()
    who = '50cent'
    last = 10
    if len(sys.argv) > 1:
        who = sys.argv[1]
        if len(sys.argv) > 2:
            last = int(sys.argv[2])
    new = Tweet.update(sess, who)
    if new > 0:
        print new,'added.'

    print 'twurp:',who
    for tweet in Tweet.latest(sess, who, last):
        print tweet.when, tweet.text
        print


Base = sql_decl.declarative_base()


def open_session(verbose=False):
    db_path = xdg_dir(['twurp','twurp.sqlite'])
    if verbose:
        print 'database:',db_path
    db_path = 'sqlite:///'+db_path
    engine = sql.create_engine(db_path, echo=verbose)
    Base.metadata.create_all(engine)
    return sql.orm.sessionmaker(engine)()


class Tweet(Base):
    __tablename__ = 'tweets'
    id = sql.Column(sql.Integer, primary_key=True)
    who = sql.Column(sql.String, nullable=False)
    when = sql.Column(sql.DateTime, nullable=False)
    text = sql.Column(sql.String, nullable=False)
    json = sql.Column(sql.String, nullable=False)

    def __init__(self, status):
        self.id = status.id
        self.who = status.user.name
        self.when = datetime.datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
        self.text = status.text
        self.json = status.AsJsonString()

    @classmethod
    def count(cls, sess, who):
        return sess.query(cls).filter(cls.who == who).count()

    @classmethod
    def latest(cls, sess, who, limit=1):
        q = sess.query(cls).filter(cls.who == who).order_by(cls.id.desc())
        if limit == 1:
            return q.first()
        return q.limit(limit)

    @classmethod
    def update(cls, sess, who):
        twit = twitter.Api()
        twurp = twit.GetUser(who)
        num_db = cls.count(sess, who)
        timeline = {}
        if num_db == 0:
            # add this guy afresh
            timeline['count'] = twurp.statuses_count
        elif num_db == twurp.statuses_count:
            return
        else:
            # find the last tweet
            last = cls.latest(sess, who)
            timeline['since_id'] = last.id

        for tweet in map(cls, twit.GetUserTimeline(who,**timeline)):
            sess.add(tweet)
        sess.commit()
        new_db = cls.count(sess, who) - num_db
        return new_db



XDG_DATA   = {'env': 'XDG_DATA_HOME',  'default': os.path.join('~','.local','share')}
XDG_CONFIG = {'env': 'XDG_CONFIG_HOME','default': os.path.join('~','.config')}
XDG_CACHE  = {'env': 'XDG_CACHE_HOME', 'default': os.path.join('~','.cache')}


def xdg_dir(path, kind=XDG_DATA):
    """path is an array of components to be joined into a single path then
    prefixed with the XDG path of the corresponding kind.
    makes all directories necessary to make the full path valid.
    """
    # XDG base data dir
    xdg_dir = os.getenv(kind['env'], kind['default'])
    prefix = os.path.expanduser(os.path.join(xdg_dir, *path[:-1]))
    try:
        os.makedirs(prefix)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise
    return os.path.join(prefix, path[-1])


if __name__ == '__main__':
    main()

