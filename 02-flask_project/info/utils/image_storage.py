from qiniu import Auth, put_data

access_key = "DTxGUHXb1XJE0T10A4ecG8iuv4E5hXqp1ymyN4x4"
secret_key = "8R-jXZHtUfP3RVWY_hagjNS6VGuOYUSCPG0nD5kG"
bucket_name = "Bape"


def storage(data):
    try:
        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)
        ret, info = put_data(token, None, data)
        print(ret, info)
    except Exception as e:
        raise e;

    if info.status_code != 200:
        raise Exception("上传图片失败")
    return ret["key"]


if __name__ == '__main__':
    file = input('请输入文件路径')
    with open(file, 'rb') as f:
        storage(f.read())
