# UserController.py
import json
import pymysql
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import hashlib
import uuid

from util.RandomUtil import generate_unique_random


@csrf_exempt
def user_login(request):
    """
    用户登录接口（只需要用户名和密码）
    数据库字段: id、name、age、phone、password
    """
    if request.method == "POST":
        try:
            # 解析请求数据
            data = json.loads(request.body.decode('utf-8'))
            username = data.get("username")  # 这里username对应数据库中的name字段
            password = data.get("password")

            # 参数校验
            if not username or not password:
                return JsonResponse({
                    "code": 400,
                    "msg": "用户名和密码不能为空"
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

            # 查询用户信息（使用name字段作为用户名）
            sql = "SELECT id, name, age, phone, password,type,faceid FROM user WHERE name = %s"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()

            if result:
                user_id, name, age, phone, hashed_password,type,faceid = result

                # 验证密码（假设密码未加密存储）
                if password == hashed_password:
                    # 登录成功
                    if type=="admin":
                        return JsonResponse({
                            "code": 300,
                            "msg": "欢迎登录管理员系统",
                            "data": {
                                "user_id": user_id,
                                "username": name,  # 返回用户名
                                "age": age,
                                "phone": phone,
                                "password": password,
                                "faceid": faceid
                            }
                        })

                    else:
                        return JsonResponse({
                            "code": 200,
                            "msg": "欢迎登录用户端",
                            "data": {
                                "user_id": user_id,
                                "username": name,  # 返回用户名
                                "age": age,
                                "phone": phone,
                                "face_id": faceid
                            }
                        })

                else:
                    # 密码错误
                    return JsonResponse({
                        "code": 401,
                        "msg": "用户名或密码错误"
                    })
            else:
                # 用户不存在
                return JsonResponse({
                    "code": 401,
                    "msg": "用户名或密码错误"
                })

        except json.JSONDecodeError:
            return JsonResponse({
                "code": 400,
                "msg": "请求数据格式错误"
            })
        except Exception as e:
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


@csrf_exempt
def user_register(request):
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
            type="user"
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


def user_logout(request):
    """
    用户登出接口
    """
    if hasattr(request, 'session'):
        request.session.flush()

    return JsonResponse({
        "code": 200,
        "msg": "登出成功"
    })


@csrf_exempt
def update_user_info(request, user_id):
    """
    更新用户信息接口
    """
    if request.method == "PUT":
        try:
            # 解析请求数据
            data = json.loads(request.body.decode('utf-8'))
            username = data.get("username")
            age = data.get("age")
            phone = data.get("phone")

            # 参数校验
            if not username or not age or not phone:
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
            update_sql = "UPDATE user SET name = %s, age = %s, phone = %s WHERE id = %s"
            cursor.execute(update_sql, (username, age, phone, user_id))

            # 提交事务
            conn.commit()

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


@csrf_exempt
def change_password(request, user_id):
    """
    修改用户密码接口
    """
    if request.method == "PUT":
        try:
            # 解析请求数据
            data = json.loads(request.body.decode('utf-8'))
            old_password = data.get("old_password")
            new_password = data.get("new_password")

            # 验证新密码
            if not new_password:
                return JsonResponse({
                    "code": 400,
                    "msg": "新密码不能为空"
                })

            if len(new_password) < 3:
                return JsonResponse({
                    "code": 400,
                    "msg": "密码长度不能少于3位"
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

            # 查询用户当前密码
            sql = "SELECT password FROM user WHERE id = %s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()

            if not result:
                return JsonResponse({
                    "code": 404,
                    "msg": "用户不存在"
                })

            current_password = result[0]

            # 检查用户是否已设置密码
            if current_password and current_password != "":
                # 用户已设置密码，需要验证原密码
                if not old_password:
                    return JsonResponse({
                        "code": 400,
                        "msg": "原密码不能为空"
                    })

                # 验证原密码
                if old_password != current_password:
                    return JsonResponse({
                        "code": 400,
                        "msg": "原密码错误"
                    })
            # 如果用户密码为空，则不需要验证原密码

            # 更新密码
            update_sql = "UPDATE user SET password = %s WHERE id = %s"
            cursor.execute(update_sql, (new_password, user_id))

            # 提交事务
            conn.commit()

            return JsonResponse({
                "code": 200,
                "msg": "密码修改成功"
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


