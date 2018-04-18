import flask_migrate
import info
# 将app与db关联
flask_migrate.Migrate(info.app, info.info_db)
info.manager.add_command('db', flask_migrate.MigrateCommand)


@info.app.route("/")
def index():
    return "index"


if __name__ == '__main__':
    info.manager.run()