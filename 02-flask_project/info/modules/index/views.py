from info.modules.index import index_blu
import info


@index_blu.route('/')
def index():
    info.redis_db.set('name', '安逸猿')
    return "index"
