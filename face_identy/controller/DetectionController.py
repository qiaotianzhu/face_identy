import uuid
import os
import cv2 as cv
import pymysql
from django.conf import settings
from django.http import JsonResponse
from ultralytics.models import YOLO
import os
import json
import base64
import time
import tkinter as tk
from tkinter import filedialog
import threading

# 获取 static 目录下的 model 文件夹路径
model_path = os.path.join(settings.BASE_DIR, 'static', 'model')
# 目标检测
# 目标检测
def predict(request):
    # 记录开始时间
    start_time = time.time()

    if request.method == "POST":
        # 获取模型参数
        select_model = request.POST.get('model', 'default_model')
        print(f"接收到的模型参数: {select_model}")
        # 根据模型名称选择不同的处理方式
        if select_model == 'model1':
            modelname = "traffic_best.pt"
        elif select_model == 'model2':
            modelname = "best_Turbines.pt"
        elif select_model == 'model3':
            modelname = "traffic_best.pt"
        else:
            # 默认模型处理
            modelname = "traffic_best.pt"
        model = YOLO(os.path.join(model_path, modelname))
        # 确认上传图片
        if "img" not in request.FILES:
            return JsonResponse({"code": 500, "msg": "没有找到图片"}, status=400)
        # 获取图片
        image_file = request.FILES["img"]
        print(f"收到的图片名是：{image_file.name}")

        # 直接从内存中读取图片，不保存到磁盘
        import numpy as np
        import base64
        from PIL import Image

        # 将上传的图片转换为numpy数组
        image_bytes = image_file.read()
        image_array = np.frombuffer(image_bytes, np.uint8)
        img = cv.imdecode(image_array, cv.IMREAD_COLOR)

        if img is None:
            return JsonResponse({"code": 500, "msg": "图片解码失败"}, status=400)

        # 使用yolo模型进行预测
        results = model(img)

        # 收集检测结果信息
        detection_info = {
            "image_name": image_file.name,
            "model_used": modelname,
            "processing_time": 0,  # 将在后面填充
            "detections": [],
            "total_detections": 0
        }

        # 处理检测结果
        if len(results) > 0 and hasattr(results[0], 'boxes') and results[0].boxes is not None:
            boxes = results[0].boxes
            # 获取类别名称（如果模型有定义）
            class_names = model.names if hasattr(model, 'names') else {}

            for i, box in enumerate(boxes):
                # 获取边界框坐标
                xyxy = box.xyxy[0].tolist() if hasattr(box, 'xyxy') else []
                # 获取置信度
                confidence = float(box.conf[0]) if hasattr(box, 'conf') and box.conf is not None else 0.0
                # 获取类别ID
                class_id = int(box.cls[0]) if hasattr(box, 'cls') and box.cls is not None else -1
                # 获取类别名称
                class_name = class_names.get(class_id, f"Class_{class_id}") if class_id >= 0 else "Unknown"

                detection_data = {
                    "detection_id": i + 1,
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": confidence,
                    "bounding_box": {
                        "x1": xyxy[0] if len(xyxy) > 0 else 0,
                        "y1": xyxy[1] if len(xyxy) > 1 else 0,
                        "x2": xyxy[2] if len(xyxy) > 2 else 0,
                        "y2": xyxy[3] if len(xyxy) > 3 else 0
                    }
                }
                detection_info["detections"].append(detection_data)

            detection_info["total_detections"] = len(detection_info["detections"])

        # 记录结束时间
        end_time = time.time()
        processing_time = end_time - start_time
        detection_info["processing_time"] = processing_time
        detection_info["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))
        detection_info["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))

        # 直接处理结果图像，不保存到文件
        result_img_array = results[0].plot()

        # 将处理后的图像转换为base64编码
        _, buffer = cv.imencode('.jpg', result_img_array)
        img_str = base64.b64encode(buffer).decode()

        # 构造返回数据
        return JsonResponse({
            "code": 200,
            "msg": "返回成功",
            "processed_img_base64": f"data:image/jpeg;base64,{img_str}",
            "detection_info": detection_info,
            "detection_summary": {
                "total_detections": detection_info["total_detections"],
                "processing_time": f"{processing_time:.2f}秒",
                "model_used": modelname
            }
        })





# 添加一个新的函数用于在后台线程中打开文件对话框
def open_directory_dialog():
    """
    在后台线程中打开目录选择对话框
    """
    # 创建一个隐藏的 tkinter 根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏根窗口
    root.attributes('-topmost', True)  # 确保对话框在最前面

    # 打开目录选择对话框
    directory = filedialog.askdirectory(title="选择保存目录")

    # 销毁根窗口
    root.destroy()

    return directory


# 修改 save_detection_result 函数
# 修改 save_detection_result 函数
def save_detection_result(request):
    """
    保存检测结果到指定路径，并记录到数据库
    """
    if request.method == "POST":
        try:
            # 获取请求数据
            data = json.loads(request.body.decode('utf-8'))
            # 注意：这里不再直接获取 save_path，而是通过对话框选择
            detection_info = data.get('detection_info', {})
            detection_summary = data.get('detection_summary', {})
            image_base64 = data.get('image_data', '')


            # 在后台线程中打开目录选择对话框
            # 使用 threading 调用 GUI 对话框
            directory = open_directory_dialog()

            # 如果用户取消了选择，directory 将为 None 或空字符串
            if not directory:
                return JsonResponse({
                    "code": 400,
                    "msg": "用户取消了保存操作"
                })

            save_path = directory

            # 创建保存目录（如果不存在）
            os.makedirs(save_path, exist_ok=True)

            # 生成时间戳用于文件名
            timestamp = int(time.time())

            # 保存图片文件
            image_filename = f"detection_result_{timestamp}.jpg"
            image_path = os.path.join(save_path, image_filename)

            # 解码base64图片数据并保存
            if image_base64.startswith('data:image'):
                # 去掉数据URL前缀
                image_data = image_base64.split(',')[1]
            else:
                image_data = image_base64

            image_bytes = base64.b64decode(image_data)
            with open(image_path, 'wb') as f:
                f.write(image_bytes)

            # 创建包含中文信息的JSON数据
            json_filename = f"detection_info_{timestamp}.json"
            json_path = os.path.join(save_path, json_filename)

            # 构造包含中文信息的完整数据
            result_data = {
                "基本信息": {
                    "标题": "目标检测结果报告",
                    "保存时间": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)),
                    "保存路径": save_path,
                    "图片文件名": image_filename,
                    "信息文件名": json_filename
                },
                "检测信息": detection_info,
                "检测摘要": detection_summary,
                "中文结果信息": {
                    "原始图片名": detection_info.get("image_name", "未知"),
                    "使用模型": detection_info.get("model_used", "未知"),
                    "检测目标数": detection_info.get("total_detections", 0),
                    "处理时间": f"{detection_info.get('processing_time', 0):.2f}秒",
                    "开始时间": detection_info.get("start_time", ""),
                    "结束时间": detection_info.get("end_time", "")
                },
                "检测详情": []
            }

            # 添加检测详情的中文描述
            detections = detection_info.get("detections", [])
            for detection in detections:
                result_data["检测详情"].append({
                    "序号": detection.get("detection_id", 0),
                    "类别ID": detection.get("class_id", -1),
                    "类别名称": detection.get("class_name", "未知"),
                    "置信度": f"{detection.get('confidence', 0) * 100:.1f}%",
                    "边界框坐标": detection.get("bounding_box", {})
                })

            # 保存JSON文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=4)

            # 准备数据库插入所需数据
            record_id = str(uuid.uuid4())  # 生成唯一ID
            user_id = data.get('user_id', '')
            starttime = detection_info.get("start_time", "")  # 开始时间
            usetime = detection_info.get("processing_time", 0.0)  # 处理时间
            model = detection_info.get("model_used", "")  # 模型名
            savepath = save_path  # 保存路径

            # 插入数据库记录
            record_insert(record_id, user_id,starttime, usetime, model, savepath)

            return JsonResponse({
                "code": 200,
                "msg": "保存成功",
                "data": {
                    "image_path": image_path,
                    "json_path": json_path,
                    "save_path": save_path
                }
            })

        except Exception as e:
            print(f"保存检测结果时出错: {e}")
            return JsonResponse({
                "code": 500,
                "msg": f"保存失败: {str(e)}"
            })
    else:
        return JsonResponse({
            "code": 400,
            "msg": "请求方式错误"
        })

def record_insert(id,user_id, starttime, usetime, model,savepath):
    try:
        conn = pymysql.connect(host="localhost", port=3306, user="root", password="123456", database="detection",
                               charset="utf8")
        # 创建游标对象
        cursor = conn.cursor()
        # 创建sql语句
        sql = "insert into record(id,user_id,starttime, usetime, model,savepath) values(%s,%s,%s,%s,%s,%s)"
        cursor.execute(sql, (id,user_id,starttime, usetime, model,savepath))
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
def record_getlist(request):
    if request.method == 'GET':
        try:
            # 从GET参数中获取user_id
            user_id = request.GET.get('user_id')
            if not user_id:
                response_data = {
                    'code': 400,
                    'msg': '缺少用户ID参数',
                    'data': []
                }
                return JsonResponse(response_data)
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
            sql = "SELECT * FROM record WHERE user_id=%s"
            cursor.execute(sql,(user_id,))
            # 获取查询结果
            records = cursor.fetchall()

            # 将结果转换为字典列表
            records_data = []
            for record in records:
                records_data.append({
                    'starttime': record[2],
                    'usetime': record[3],
                    'model': record[4],
                    'savepath': record[5],
                })

            # 关闭游标和连接
            cursor.close()
            conn.close()

            # 构造返回数据
            response_data = {
                'code': 200,
                'msg': '获取记录列表成功',
                'data': records_data
            }

            return JsonResponse(response_data)

        except Exception as e:
            # 异常处理
            response_data = {
                'code': 500,
                'msg': f'获取记录列表失败: {str(e)}',
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


def record_clear(request):
    if request.method == 'DELETE':
        try:
            # 从GET参数中获取user_id
            user_id = request.GET.get('user_id')
            if not user_id:
                response_data = {
                    'code': 400,
                    'msg': '缺少用户ID参数',
                    'data': []
                }
                return JsonResponse(response_data)

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

            # 执行删除语句，根据user_id删除记录
            sql = "DELETE FROM record WHERE user_id=%s"
            cursor.execute(sql, (user_id,))

            # 获取删除的记录数
            deleted_count = cursor.rowcount

            # 提交事务
            conn.commit()

            # 关闭游标和连接
            cursor.close()
            conn.close()

            # 构造返回数据
            response_data = {
                'code': 200,
                'msg': f'成功清空{deleted_count}条记录',
                'data': []
            }

            return JsonResponse(response_data)

        except Exception as e:
            # 异常处理
            response_data = {
                'code': 500,
                'msg': f'清空记录失败: {str(e)}',
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


