import os
import uuid
from ultralytics import YOLO
import face_recognition
from django.conf import settings
from django.contrib.admin.templatetags.admin_list import results
from django.http import JsonResponse
from util.ImageUtil import *
import cv2 as cv
import numpy as np
import pymysql
from util.RandomUtil import generate_unique_random
import json
import re

localImage_path = os.path.join(settings.BASE_DIR, 'static', 'localImage/')
# 定义人脸图片存储路径
face_url = localImage_path


# 人脸信息采集
def face_collection(request):
    if request.method == "POST":
        try:
            # 获取人脸图片矩阵
            image_array = get_image_array(request)
            print(image_array)
            # 把人脸图片转换为rgb格式
            image = cv.cvtColor(image_array, cv.COLOR_BGR2RGB)
            # 获取人脸位置信息
            face_locations = face_recognition.face_locations(image)
            if len(face_locations) == 0:
                data = {
                    "code": 500,
                    "msg": "未检测到人脸",
                }
                return JsonResponse(data)
            else:
                # 获取图像的二进制码
                image_byte = get_image_byte(request)
                # 为图片生成唯一文件名
                name_id = generate_unique_random(min_num=1, max_num=1000)


                # 把数据转换成字典
                data = json.loads(request.body.decode('utf-8'))
                print(data)

                # 读取用户输入的信息
                name = data.get("name", "").strip()
                age = data.get("age", "").strip()
                phone = data.get("phone", "").strip()

                # 参数校验 - 空值检查
                if not name or not age or not phone:
                    return JsonResponse({
                        "code": 400,
                        "msg": "所有字段都不能为空"
                    })

                # 用户名校验
                if len(name) < 2 or len(name) > 20:
                    return JsonResponse({
                        "code": 400,
                        "msg": "用户名长度必须在2-20个字符之间"
                    })

                # 用户名格式校验（只允许中文、英文、数字和下划线）
                if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_]+$', name):
                    return JsonResponse({
                        "code": 400,
                        "msg": "用户名只能包含中文、英文、数字和下划线"
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

                # 验证手机号格式
                if not re.match(r'^1[3-9]\d{9}$', phone):
                    return JsonResponse({
                        "code": 400,
                        "msg": "手机号格式不正确"
                    })

                # 检查用户名是否已存在
                user_result = queryByName(name)
                if user_result:
                    return JsonResponse({
                        "code": 400,
                        "msg": "用户名已存在"
                    })

                # 检查手机号是否已存在
                phone_result = queryByPhone(phone)
                if phone_result:
                    return JsonResponse({
                        "code": 400,
                        "msg": "手机号已被注册"
                    })

                print(name, age, phone)
                result = face_insert(name_id, name, age, phone)
                if result == True:
                    # 文件写入人脸图片
                    with open(face_url + str(name_id) + ".jpg", "wb") as f:
                        f.write(image_byte)
                    data = {
                        "code": 200,
                        "msg": "人脸采集成功",
                    }
                    return JsonResponse(data)
                else:
                    return JsonResponse({
                        "code": 500,
                        "msg": "数据保存失败，请稍后重试"
                    })
        except json.JSONDecodeError:
            return JsonResponse({
                "code": 400,
                "msg": "请求数据格式错误"
            })
        except Exception as e:
            print(f"人脸采集过程中出错: {e}")
            return JsonResponse({
                "code": 500,
                "msg": "系统错误，请稍后重试"
            })
    else:
        data = {
            "code": 400,
            "msg": "请求方式错误",
        }
        return JsonResponse(data)


def face_detection(request):
    if request.method == "POST":
        # 获取人脸图片矩阵
        image_array = get_image_array(request)
        print(image_array)
        # 把人脸图片转换为rgb格式
        image = cv.cvtColor(image_array, cv.COLOR_BGR2RGB)
        # 获取人脸位置信息
        face_locations = face_recognition.face_locations(image)
        # 获取摄像头中人脸的编码
        image_v = face_recognition.face_encodings(image)[0]
        if len(face_locations) == 0:
            data = {
                "code": 500,
                "msg": "未检测到人脸",
            }
            return JsonResponse(data)
        # 获取所有录入的图像
        else:
            # 获取已录入图像的文件名列表
            face_dir = os.listdir(face_url)
            for face in face_dir:
                # 定义路径
                face_path = face_url + face
                # 加载图像
                face_image = face_recognition.load_image_file(face_path)
                # 获取图像编码
                face_v = face_recognition.face_encodings(face_image)[0]
                # 计算相似度
                d = np.linalg.norm(image_v - face_v)
                print(d)

                if d < 0.5:
                    num = int(face.split(".")[0])
                    result = query_info(num)
                    if result:
                        # 修改返回的数据结构，与前端期望的格式一致
                        data = {
                            "code": 200,
                            "msg": f"登陆成功！欢迎进入系统！",
                            "data": {
                                "user_id": str(num),  # 确保是字符串格式
                                "username": result[0],  # 返回用户名
                                "age": result[1],
                                "phone": result[2],
                                "password":result[3],
                                "face_id": result[5] if result[5] else ""
                            },
                            "redirect_url": "detection_detect.html",
                        }
                    else:
                        # 处理查询结果为空的情况
                        data = {
                            "code": 500,
                            "msg": "用户信息查询失败",
                        }
                    return JsonResponse(data)
            data = {
                "code": 500,
                "msg": "未找到匹配用户",
            }
            return JsonResponse(data)

    else:
        data = {
            "code": 400,
            "msg": "请求方式错误",
        }
        return JsonResponse(data)







def add_face(request):
    if request.method == "POST":
        try:
            # 获取人脸图片矩阵
            image_array = get_image_array(request)
            print(image_array)
            # 把人脸图片转换为rgb格式
            image = cv.cvtColor(image_array, cv.COLOR_BGR2RGB)
            # 获取人脸位置信息
            face_locations = face_recognition.face_locations(image)
            if len(face_locations) == 0:
                data = {
                    "code": 500,
                    "msg": "未检测到人脸",
                }
                return JsonResponse(data)
            else:
                # 获取图像的二进制码
                image_byte = get_image_byte(request)
                # 把数据转换成字典
                data = json.loads(request.body.decode('utf-8'))

                # 获取用户ID
                user_id = data.get("user_id")
                if not user_id:
                    return JsonResponse({
                        "code": 400,
                        "msg": "用户ID不能为空"
                    })

                faceid = user_id
                result = updateFaceid(user_id, faceid)  # 修正函数名
                if result == True:
                    # 文件写入人脸图片
                    with open(face_url + str(faceid) + ".jpg", "wb") as f:
                        f.write(image_byte)
                    data = {
                        "code": 200,
                        "msg": "人脸采集成功",
                    }
                    return JsonResponse(data)
                else:
                    return JsonResponse({
                        "code": 500,
                        "msg": "数据保存失败，请稍后重试"
                    })
        except json.JSONDecodeError:
            return JsonResponse({
                "code": 400,
                "msg": "请求数据格式错误"
            })
        except Exception as e:
            print(f"人脸采集过程中出错: {e}")
            return JsonResponse({
                "code": 500,
                "msg": "系统错误，请稍后重试"
            })
    else:
        data = {
            "code": 400,
            "msg": "请求方式错误",
        }
        return JsonResponse(data)


def queryByName(name):
    try:
        conn = pymysql.connect(host="localhost", port=3306, user="root", password="123456", database="detection",
                               charset="utf8")
        # 创建游标对象
        cursor = conn.cursor()
        # 创建sql语句
        sql = "select id from user where name=%s"
        # 执行sql语句
        cursor.execute(sql, (name,))
        # 获取查询结果
        result = cursor.fetchall()
        print(result)
        return result
    except Exception as e:
        print(e)
        return None
# 定义数据库写入操作
def face_insert(id, name, age, phone):
    try:
        conn = pymysql.connect(host="localhost", port=3306, user="root", password="123456", database="detection",
                               charset="utf8")
        # 创建游标对象
        cursor = conn.cursor()
        # 创建sql语句
        sql = "insert into user(id,name,age,phone,type,faceid) values(%s,%s,%s,%s,%s,%s)"
        # 执行sql语句
        type="user"
        faceid=id
        cursor.execute(sql, (id, name, age, phone,type,faceid))
        # 提交事务
        conn.commit()
        print("数据写入成功")
        return True
    except Exception as e:
        print(e)
        # 回滚事务
        conn.rollback()
        print("数据写入失败")
        return False
def updateFaceid(user_id,faceid):
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

        update_sql = "UPDATE user SET faceid = %s WHERE id = %s"
        cursor.execute(update_sql, (faceid, user_id))
        # 提交事务
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return None

def queryByPhone(phone):
    try:
        conn = pymysql.connect(host="localhost", port=3306, user="root", password="123456", database="detection",
                               charset="utf8")
        # 创建游标对象
        cursor = conn.cursor()
        # 创建sql语句
        sql = "select id from user where phone=%s"
        # 执行sql语句
        cursor.execute(sql, (phone,))
        # 获取查询结果
        result = cursor.fetchall()
        print(result)
        return result
    except Exception as e:
        print(e)
        return None


def query_info(id):
    try:
        conn = pymysql.connect(host="localhost", port=3306, user="root", password="123456", database="detection",
                               charset="utf8")
        # 创建游标对象
        cursor = conn.cursor()
        # 创建sql语句
        # 在查询用户信息的地方，确保SQL语句正确
        sql = "SELECT name, age, phone, password, type, faceid FROM user WHERE id=%s"

        # 执行sql语句
        cursor.execute(sql, (id,))
        # 获取查询结果
        result = cursor.fetchone()
        print(result)
        return result
    except Exception as e:
        print(e)
        return None


if __name__ == '__main__':
    # face_insert(1,"张三",18,"12345678901")
    query_info(1)
