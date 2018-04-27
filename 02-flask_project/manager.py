import flask
import flask_migrate
import flask_script
import info.models
from info import db
from info.models import User

app = info.create_app('development')
manager = flask_script.Manager(app)
# 将app与db关联
flask_migrate.Migrate(app, db)
manager.add_command('db', flask_migrate.MigrateCommand)


@manager.option('-n', '-name', dest='name')
@manager.option('-p', '-password', dest='password')
def create_super_user(name, password):
    if not all([name, password]):
        print('参数不足')

    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
    print('添加成功')


if __name__ == '__main__':
    print(app.url_map)
    manager.run()
