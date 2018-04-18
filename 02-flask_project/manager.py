import flask_migrate
import flask_script
import info.models

app = info.create_app('development')
manager = flask_script.Manager(app)
# 将app与db关联
flask_migrate.Migrate(app, info.db)
manager.add_command('db', flask_migrate.MigrateCommand)


if __name__ == '__main__':
    manager.run()
