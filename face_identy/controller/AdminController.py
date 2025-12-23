# AdminController.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pymysql
import os

from face_identy import settings
from util.RandomUtil import generate_unique_random, remove_generated_number


@csrf_exempt
def user_getlist(request):
    """
    获取用户列表方法
    """
    if request.method == 'GET':
        try:
            # 建立数据库连接
            conn = pymysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="123456",
                database="detection",
                charset="utf8"
            )

            # 创建游标对象
            cursor = conn.cursor()

            # 执行查询语句
            sql = "SELECT id, name,age,phone,password,type FROM user"  # 假设用户表名为user
            cursor.execute(sql)

            # 获取查询结果
            users = cursor.fetchall()

            # 将结果转换为字典列表
            users_data = []
            for user in users:
                users_data.append({
                    'id': user[0],
                    'username': user[1]
                    , 'age': user[2],
                    'phone': user[3],
                    'password': user[4],
                    'user_type': user[5]
                })

            # 关闭游标和连接
            cursor.close()
            conn.close()

            # 构造返回数据
            response_data = {
                'code': 200,
                'msg': '获取用户列表成功',
                'data': users_data
            }

            return JsonResponse(response_data)

        except Exception as e:
            # 异常处理
            response_data = {
                'code': 500,
                'msg': f'获取用户列表失败: {str(e)}',
                'data': []
            }
            return JsonResponse(response_data)

    else:
        # 请求方法不被允许
        response_data = {
            'code': 405,
            'msg': '请求方法不被允许',
            'data': []
        }
        return JsonResponse(response_data)
def user_add(request):
    """
    用户注册接口
    数据库字段: id、name、age、phone、password
    """
    if request.method == "POST":
        try:
            # 解析请求数据
            data = json.loads(request.body.decode('utf-8'))
            username = data.get("username")
            password = data.get("password")
            age = data.get("age")
            phone = data.get("phone")
            type=data.get("user_type")

            # 参数校验
            if not username or not password or not age or not phone:
                return JsonResponse({
                    "code": 400,
                    "msg": "所有字段都不能为空"
                })

            # 验证手机号格式
            if not phone.isdigit() or len(phone) != 11:
                return JsonResponse({
                    "code": 400,
                    "msg": "手机号格式不正确"
                })

            # 验证年龄
            try:
                age = int(age)
                if age < 1 or age > 150:
                    return JsonResponse({
                        "code": 400,
                        "msg": "年龄必须在1-150之间"
                    })
            except ValueError:
                return JsonResponse({
                    "code": 400,
                    "msg": "年龄必须是数字"
                })

            # 连接数据库
            conn = pymysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="123456",
                database="detection",
                charset="utf8"
            )

            # 创建游标对象
            cursor = conn.cursor()

            # 检查用户名是否已存在
            check_sql = "SELECT id FROM user WHERE name = %s"
            cursor.execute(check_sql, (username,))
            if cursor.fetchone():
                return JsonResponse({
                    "code": 400,
                    "msg": "用户名已存在"
                })

            # 检查手机号是否已存在
            check_sql = "SELECT id FROM user WHERE phone = %s"
            cursor.execute(check_sql, (phone,))
            if cursor.fetchone():
                return JsonResponse({
                    "code": 400,
                    "msg": "手机号已被注册"
                })

            # 插入新用户
            insert_sql = "INSERT INTO user (id, name, age, phone, password,type,faceid) VALUES (%s, %s, %s, %s, %s,%s,%s)"
            # 生成ID
            user_id=generate_unique_random(min_num=1,max_num=1000)
            faceid=user_id
            cursor.execute(insert_sql, (user_id, username, age, phone, password,type,faceid))
            # 提交事务
            conn.commit()

            return JsonResponse({
                "code": 200,
                "msg": "注册成功"
            })

        except json.JSONDecodeError:
            return JsonResponse({
                "code": 400,
                "msg": "请求数据格式错误"
            })
        except Exception as e:
            # 回滚事务
            if 'conn' in locals():
                conn.rollback()
            return JsonResponse({
                "code": 500,
                "msg": f"服务器内部错误: {str(e)}"
            })
        finally:
            # 关闭数据库连接
            if 'conn' in locals():
                conn.close()
    else:
        return JsonResponse({
            "code": 405,
            "msg": "请求方法不允许"
        })
def user_getuser(request, user_id):
    """
    用户获取接口
    数据库字段: id、name、age、phone、password
    """
    if request.method == "GET":
        try:
            # 连接数据库
            conn = pymysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="123456",
                database="detection",
                charset="utf8"
            )

            # 创建游标对象
            cursor = conn.cursor()

            # 搜索用户信息
            check_sql = "SELECT id, name, age, phone, password, type, faceid FROM user WHERE id = %s"
            cursor.execute(check_sql, (user_id,))
            result = cursor.fetchone()
            if not result:
                return JsonResponse({
                    "code": 404,
                    "msg": "用户不存在"
                })
            user_id, name, age, phone, hashed_password, type, faceid = result
            # 关闭游标和连接
            cursor.close()
            conn.close()
            return JsonResponse({
                "code": 200,
                "msg": "用户信息获取成功",
                "data":{
                    "id": user_id,
                    "username": name,  # 返回用户名
                    "age": age,
                    "phone": phone
                }
            })
        except Exception as e:
            # 回滚事务
            if 'conn' in locals():
                conn.rollback()
            # 关闭数据库连接
            if 'conn' in locals():
                conn.close()
            return JsonResponse({
                "code": 500,
                "msg": f"服务器内部错误: {str(e)}"
            })
    else:
        if request.method == "PUT":
            try:
                # 解析请求数据
                data = json.loads(request.body.decode('utf-8'))
                username = data.get("username")
                password = data.get("password")
                age = data.get("age")
                phone = data.get("phone")

                # 参数校验
                if not username or not password or not age or not phone:
                    return JsonResponse({
                        "code": 400,
                        "msg": "所有字段都不能为空"
                    })

                # 验证手机号格式
                if not phone.isdigit() or len(phone) != 11:
                    return JsonResponse({
                        "code": 400,
                        "msg": "手机号格式不正确"
                    })

                # 验证年龄
                try:
                    age = int(age)
                    if age < 1 or age > 150:
                        return JsonResponse({
                            "code": 400,
                            "msg": "年龄必须在1-150之间"
                        })
                except ValueError:
                    return JsonResponse({
                        "code": 400,
                        "msg": "年龄必须是数字"
                    })

                # 连接数据库
                conn = pymysql.connect(
                    host="localhost",
                    port=3306,
                    user="root",
                    password="123456",
                    database="detection",
                    charset="utf8"
                )

                # 创建游标对象
                cursor = conn.cursor()

                # 检查用户是否存在
                check_sql = "SELECT id FROM user WHERE id = %s"
                cursor.execute(check_sql, (user_id,))
                if not cursor.fetchone():
                    return JsonResponse({
                        "code": 404,
                        "msg": "用户不存在"
                    })

                # 检查用户名是否已被其他用户使用
                check_sql = "SELECT id FROM user WHERE name = %s AND id != %s"
                cursor.execute(check_sql, (username, user_id))
                if cursor.fetchone():
                    return JsonResponse({
                        "code": 400,
                        "msg": "用户名已被其他用户使用"
                    })

                # 检查手机号是否已被其他用户使用
                check_sql = "SELECT id FROM user WHERE phone = %s AND id != %s"
                cursor.execute(check_sql, (phone, user_id))
                if cursor.fetchone():
                    return JsonResponse({
                        "code": 400,
                        "msg": "手机号已被其他用户注册"
                    })

                # 更新用户信息
                update_sql = "UPDATE user SET name = %s, age = %s, phone = %s, password = %s WHERE id = %s"
                cursor.execute(update_sql, (username, age, phone, password, user_id))

                # 提交事务
                conn.commit()

                # 关闭游标和连接
                cursor.close()
                conn.close()

                return JsonResponse({
                    "code": 200,
                    "msg": "用户信息更新成功"
                })

            except json.JSONDecodeError:
                return JsonResponse({
                    "code": 400,
                    "msg": "请求数据格式错误"
                })
            except Exception as e:
                # 回滚事务
                if 'conn' in locals():
                    conn.rollback()
                # 关闭数据库连接
                if 'conn' in locals():
                    conn.close()
                return JsonResponse({
                    "code": 500,
                    "msg": f"服务器内部错误: {str(e)}"
                })
        else:
            return JsonResponse({
                "code": 405,
                "msg": "请求方法不允许"
            })


@csrf_exempt
def user_delete(request, user_id):
    """
    用户删除接口
    根据用户ID删除指定用户
    """
    if request.method == "DELETE":
        try:
            # 连接数据库
            conn = pymysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="123456",
                database="detection",
                charset="utf8"
            )

            # 创建游标对象
            cursor = conn.cursor()

            # 检查用户是否存在
            check_sql = "SELECT id FROM user WHERE id = %s"
            cursor.execute(check_sql, (user_id,))
            if not cursor.fetchone():
                return JsonResponse({
                    "code": 404,
                    "msg": "用户不存在"
                })

            # 删除用户
            delete_sql = "DELETE FROM user WHERE id = %s"
            cursor.execute(delete_sql, (user_id,))
            #同时删除随机数id和面部信息
            remove_generated_number(user_id)
            # 删除用户相关的图片文件

            # 构建图片文件路径
            image_path = os.path.join(settings.BASE_DIR, 'static', f'localImage/{user_id}.jpg')
            # 如果文件存在则删除
            if os.path.exists(image_path):
                os.remove(image_path)
            # 提交事务
            conn.commit()

            # 关闭游标和连接
            cursor.close()
            conn.close()

            return JsonResponse({
                "code": 200,
                "msg": "用户删除成功"
            })

        except Exception as e:
            # 回滚事务
            if 'conn' in locals():
                conn.rollback()
            # 关闭数据库连接
            if 'conn' in locals():
                conn.close()
            return JsonResponse({
                "code": 500,
                "msg": f"服务器内部错误: {str(e)}"
            })
    else:
        return JsonResponse({
            "code": 405,
            "msg": "请求方法不允许"
        })



