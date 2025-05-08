from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import glfw
import math

lines = [] 
polygons = [] 
fixed_points = []  
current_point = None  
draw_mode = None  
selected_object = None # 当前选中的对象 {'type': 'line'/'polygon', 'index': int}
selected_point = None
current_color = (0.0, 0.0, 0.0) # 默认黑色
scale_factor = 1.0  
is_drawing = False  
is_dragging = False  
is_scaling = False
drag_offset = (0, 0) 
window_width, window_height = 800, 600

color_palette = {
    '1': (0.0, 0.0, 0.0),   # 黑
    '2': (1.0, 0.0, 0.0),   # 红
    '3': (0.0, 1.0, 0.0),   # 绿
    '4': (0.0, 0.0, 1.0),   # 蓝
    '5': (1.0, 1.0, 0.0),   # 黄
    '6': (1.0, 0.0, 1.0),   # 紫
    '7': (0.0, 1.0, 1.0),   # 青
    '8': (1.0, 1.0, 1.0),   # 白
    '9': (1.0, 0.5, 0.0)    # 橙
}

def init():
    glClearColor(1.0, 1.0, 1.0, 1.0)  # 白色背景
    # glColor3f(*current_color)  

    # 启用反走样
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)
    glEnable(GL_POINT_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)

    glPointSize(4.0)
    glLineWidth(3.0)
    # glMatrixMode(GL_PROJECTION) # 设置投影矩阵
    # glLoadIdentity()
    # gluOrtho2D(0.0, window_width, 0.0, window_height) # 2D正交投影

def pixel_to_ndc(x_pixel, y_pixel, width, height):
    """将窗口像素坐标转换为标准坐标系"""
    x_ndc = 2.0 * x_pixel / width - 1.0
    y_ndc = 2.0 * y_pixel / height - 1.0
    return (x_ndc, y_ndc)

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    
    # 绘制所有已确定的点
    glColor3f(*current_color)
    if fixed_points:
        glBegin(GL_POINTS)
        for point in fixed_points:
            glVertex2f(point[0], point[1])
        glEnd()
    
     # 绘制所有直线
    for i, line in enumerate(lines):
        if selected_object and selected_object['type'] == 'line' and selected_object['index'] == i:
            glColor3f(0.5, 0.5, 0.5)  # 选中状态显示灰色
        else:
            glColor3f(line['color'][0], line['color'][1], line['color'][2])
        glBegin(GL_LINES)
        glVertex2f(line['points'][0][0], line['points'][0][1])
        glVertex2f(line['points'][1][0], line['points'][1][1])
        glEnd()

    # 绘制所有多边形
    for i, polygon in enumerate(polygons):
        if selected_object and selected_object['type'] == 'polygon' and selected_object['index'] == i:
            glColor3f(0.5, 0.5, 0.5)  # 选中状态显示灰色
        else:
            glColor3f(polygon['color'][0], polygon['color'][1], polygon['color'][2])
        glBegin(GL_POLYGON)
        for point in polygon['points']:
            glVertex2f(point[0], point[1])
        glEnd()

        # 绘制多边形边框
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_LINE_LOOP)
        for point in polygon['points']:
            glVertex2f(point[0], point[1])
        glEnd()
    
    # 绘制当前正在绘制的图形
    glColor3f(*current_color)
    if draw_mode == 'line' and len(fixed_points) == 1 and current_point:
        glBegin(GL_LINES)
        glVertex2f(fixed_points[0][0], fixed_points[0][1])
        glVertex2f(current_point[0], current_point[1])
        glEnd()
    elif draw_mode == 'polygon' and fixed_points:
        glBegin(GL_LINE_STRIP)
        for point in fixed_points:
            glVertex2f(point[0], point[1])
        if current_point:
            glVertex2f(current_point[0], current_point[1])
        glEnd()
    
    glutSwapBuffers()

def render(window):
    glClear(GL_COLOR_BUFFER_BIT)
    # 绘制所有已确定的点
    glColor3f(*current_color)
    if fixed_points:
        glBegin(GL_POINTS)
        for point in fixed_points:
            glVertex2f(point[0], point[1])
        glEnd()
    
    # 绘制所有直线
    for i, line in enumerate(lines):
        if selected_object and selected_object['type'] == 'line' and selected_object['index'] == i:
            glColor3f(0.5, 0.5, 0.5)  # 选中状态显示灰色
        else:
            glColor3f(*line['color'])
        glBegin(GL_LINES)
        for point in line['points']:
            glVertex2f(point[0], point[1])
        glEnd()

    # 绘制所有多边形
    for i, polygon in enumerate(polygons):
        if selected_object and selected_object['type'] == 'polygon' and selected_object['index'] == i:
            glColor3f(0.5, 0.5, 0.5)  # 选中状态显示灰色
        else:
            glColor3f(*polygon['color'])
        glBegin(GL_POLYGON)
        for point in polygon['points']:
            glVertex2f(point[0], point[1])
        glEnd()

        # 绘制多边形边框
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_LINE_LOOP)
        for point in polygon['points']:
            glVertex2f(point[0], point[1])
        glEnd()
    
    # 绘制当前正在绘制的图形
    glColor3f(*current_color)
    if draw_mode == 'line' and len(fixed_points) == 1 and current_point:
        glBegin(GL_LINES)
        glVertex2f(fixed_points[0][0], fixed_points[0][1])
        glVertex2f(current_point[0], current_point[1])
        glEnd()
    elif draw_mode == 'polygon' and fixed_points:
        glBegin(GL_LINE_STRIP)
        for point in fixed_points:
            glVertex2f(point[0], point[1])
        if current_point:
            glVertex2f(current_point[0], current_point[1])
        glEnd()
    
    glfw.swap_buffers(window)

def click(button, state, x, y):
    global fixed_points, is_drawing, selected_object, is_dragging, drag_offset, is_scaling, selected_point, polygons

    y = window_height - y  # 坐标转换（GL坐标系y轴向下）
    
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            if draw_mode == 'select':
                select_object(x, y)
                if selected_object:
                    is_dragging = True
                    if selected_object['type'] == 'line':
                        line = lines[selected_object['index']]
                        drag_offset = (line['points'][0][0] - x, line['points'][0][1] - y)
                    else:
                        polygon = polygons[selected_object['index']]
                        center = get_center(polygon['points'])
                        drag_offset = (center[0] - x, center[1] - y)

            elif draw_mode == 'line':
                if not is_drawing: 
                    fixed_points = [(x, y)]
                    is_drawing = True
                else: 
                    fixed_points.append((x, y))
                    lines.append({
                        'points': fixed_points.copy(),
                        'color': current_color
                    })
                    fixed_points = []
                    is_drawing = False

            elif draw_mode == 'polygon':
                is_drawing = True
                is_closed, polygon = check_polygon_closure(fixed_points, (x, y), threshold=10)
                if is_closed:
                    polygons.append({
                        'points': fixed_points.copy(),
                        'color': current_color
                    })
                    fixed_points = []
                    is_drawing = False
                else:
                    fixed_points.append((x, y))
           

        elif state == GLUT_UP and is_dragging:
            is_dragging = False
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        print("按住右键")
        is_scaling = True
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_UP:
        print("松开右键")
        is_scaling = False
    
    glutPostRedisplay()

def mouse_button_callback(window, button, action, mods):
    global fixed_points, is_drawing, selected_object, is_dragging, drag_offset, is_scaling, selected_point, polygons

    x, y = glfw.get_cursor_pos(window)
    y = window_height - y  # 坐标转换

    x, y = pixel_to_ndc(x, y, window_width, window_height)
    
    # 左键处理
    if button == glfw.MOUSE_BUTTON_LEFT:
        if action == glfw.PRESS:
            if draw_mode == 'select':
                select_object(x, y) 
                if selected_object:
                    is_dragging = True
                    if selected_object['type'] == 'line':
                        line = lines[selected_object['index']]
                        drag_offset = (line['points'][0][0] - x, line['points'][0][1] - y)
                    else:
                        polygon = polygons[selected_object['index']]
                        center = get_center(polygon['points'])  # 假设 get_center 已实现
                        drag_offset = (center[0] - x, center[1] - y)

            elif draw_mode == 'line':
                if not is_drawing:
                    fixed_points = [(x, y)]
                    is_drawing = True
                else:
                    fixed_points.append((x, y))
                    lines.append({
                        'points': fixed_points.copy(),
                        'color': current_color
                    })
                    fixed_points = []
                    is_drawing = False

            elif draw_mode == 'polygon':
                is_drawing = True
                is_closed, polygon = check_polygon_closure(fixed_points, (x, y))
                if is_closed:
                    polygons.append({
                        'points': fixed_points.copy(),
                        'color': current_color
                    })
                    fixed_points = []
                    is_drawing = False
                else:
                    fixed_points.append((x, y))

        elif action == glfw.RELEASE and is_dragging:
            is_dragging = False

    # 右键处理（缩放）
    elif button == glfw.MOUSE_BUTTON_RIGHT:
        if action == glfw.PRESS:
            print("按住右键")
            is_scaling = True
        elif action == glfw.RELEASE:
            print("松开右键")
            is_scaling = False

def move(x, y):
    global current_point, selected_object, polygons
    
    y = window_height - y  
    current_point = (x, y)
    
    if is_dragging and selected_object:
        if selected_object['type'] == 'line':
            line = lines[selected_object['index']]
            dx = x + drag_offset[0] - line['points'][0][0]
            dy = y + drag_offset[1] - line['points'][0][1]
            for i in range(2):
                line['points'][i] = (line['points'][i][0] + dx, line['points'][i][1] + dy)
        elif selected_object['type'] == 'polygon':
            polygon = polygons[selected_object['index']]
            dx = x + drag_offset[0] - get_center(polygon['points'])[0]
            dy = y + drag_offset[1] - get_center(polygon['points'])[1]
            for i in range(len(polygon['points'])):
                polygon['points'][i] = (polygon['points'][i][0] + dx, polygon['points'][i][1] + dy)

    glutPostRedisplay()

def cursor_pos_callback(window, x, y):
    global current_point, selected_object, polygons, is_dragging, drag_offset

    # 坐标转换（GLFW 的 y 向下，OpenGL 的 y 向上）
    y = window_height - y
    x, y = pixel_to_ndc(x, y, window_width, window_height)
    current_point = (x, y)

    if is_dragging and selected_object:
        if selected_object['type'] == 'line':
            line = lines[selected_object['index']]
            dx = x + drag_offset[0] - line['points'][0][0]
            dy = y + drag_offset[1] - line['points'][0][1]
            for i in range(len(line['points'])):
                line['points'][i] = (line['points'][i][0] + dx, line['points'][i][1] + dy)
        elif selected_object['type'] == 'polygon':
            polygon = polygons[selected_object['index']]
            dx = x + drag_offset[0] - get_center(polygon['points'])[0]
            dy = y + drag_offset[1] - get_center(polygon['points'])[1]
            for i in range(len(polygon['points'])):
                polygon['points'][i] = (polygon['points'][i][0] + dx, polygon['points'][i][1] + dy)

def keyboard(key, x, y):
    global fixed_points, is_drawing, draw_mode, current_color, lines, polygons, current_point, scale_factor
    
    key = key.decode('utf-8').lower()
    
    if key == 'l':  # 直线模式
        draw_mode = 'line'
        fixed_points = []
        is_drawing = False
        print("直线模式 - 点击左键绘制直线段")
    
    elif key == 'p':  # 多边形模式
        draw_mode = 'polygon'
        fixed_points = []
        is_drawing = False
        print("多边形模式 - 点击左键添加顶点，右键结束")
    
    elif key == 'c':  # 清除
        fixed_points = []
        current_point = None
        current_color = color_palette['1']
        scale_factor = 1.0
        is_drawing = False
        lines = []
        polygons = []
        print("清除所有图形")

    elif key == 's':  # 选择模式
        draw_mode = 'select'
        fixed_points = []
        is_drawing = False
        print("选择模式 - 点击选择对象，可拖动和缩放")

    elif key in color_palette:  # 颜色选择
        current_color = color_palette[key]
        if draw_mode == "select":
            if selected_object['type'] == "line":
                lines[selected_object['index']]['color'] = current_color
            elif selected_object['type'] == "polygon": 
                polygons[selected_object['index']]['color'] = current_color
        color_name = {
            '1': '黑色', '2': '红色', '3': '绿色', '4': '蓝色',
            '5': '黄色', '6': '紫色', '7': '青色', '8': '白色', '9': '橙色'
        }[key]
        print(f"当前颜色: {color_name} {current_color}")
    
    elif key == 'q':
        if(scale_factor < 1.0):
            scale_factor = 1.0
        scale_object(1.2)
    elif key == 'e':
        if(scale_factor > 1.0):
            scale_factor = 1.0
        scale_object(0.8)

    glutPostRedisplay()

def key_callback(window, key, scancode, action, mods):
    global fixed_points, is_drawing, draw_mode, current_color, lines, polygons, current_point, scale_factor

    if action != glfw.PRESS:
        return

    key_mapping = {
        glfw.KEY_L: 'l',
        glfw.KEY_P: 'p',
        glfw.KEY_C: 'c',
        glfw.KEY_S: 's',
        glfw.KEY_Q: 'q',
        glfw.KEY_E: 'e',
        glfw.KEY_1: '1',
        glfw.KEY_2: '2',
        glfw.KEY_3: '3',
        glfw.KEY_4: '4',
        glfw.KEY_5: '5',
        glfw.KEY_6: '6',
        glfw.KEY_7: '7',
        glfw.KEY_8: '8',
        glfw.KEY_9: '9'
    }

    key_char = key_mapping.get(key, '')

    if key_char == 'l':
        draw_mode = 'line'
        fixed_points = []
        is_drawing = False
        print("直线模式 - 点击左键绘制直线段")

    elif key_char == 'p': 
        draw_mode = 'polygon'
        fixed_points = []
        is_drawing = False
        print("多边形模式 - 点击左键添加顶点，右键结束")

    elif key_char == 'c': 
        fixed_points = []
        current_point = None
        current_color = color_palette['1']
        scale_factor = 1.0
        is_drawing = False
        lines = []
        polygons = []
        print("清除所有图形")

    elif key_char == 's': 
        draw_mode = 'select'
        fixed_points = []
        is_drawing = False
        print("选择模式 - 点击选择对象，可拖动和缩放")

    elif key_char in color_palette: 
        current_color = color_palette[key_char]
        if draw_mode == "select" and selected_object:
            if selected_object['type'] == "line":
                lines[selected_object['index']]['color'] = current_color
            elif selected_object['type'] == "polygon":
                polygons[selected_object['index']]['color'] = current_color
        color_name = {
            '1': '黑色', '2': '红色', '3': '绿色', '4': '蓝色',
            '5': '黄色', '6': '紫色', '7': '青色', '8': '白色', '9': '橙色'
        }.get(key_char, '未知')
        print(f"当前颜色: {color_name} {current_color}")

    elif key_char == 'q':  # 放大
        if scale_factor < 1.0:
            scale_factor = 1.0
        scale_object(1.2) 

    elif key_char == 'e':  # 缩小
        if scale_factor > 1.0:
            scale_factor = 1.0
        scale_object(0.8)

    elif key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)

def scale_object(factor):
    global scale_factor, selected_object, polygons, lines

    if selected_object and selected_object['type'] == 'polygon':
        scale_factor *= factor
        print(f"scale: {scale_factor}")
        polygon = polygons[selected_object['index']]
        center = get_center(polygon['points'])
        for i in range(len(polygon['points'])):
            polygon['points'][i] = (
                center[0] + (polygon['points'][i][0] - center[0]) * scale_factor,
                center[1] + (polygon['points'][i][1] - center[1]) * scale_factor
            )
            
    glutPostRedisplay()

def is_near(point, target, threshold=0.05):
    distance = math.sqrt((point[0] - target[0]) ** 2 + (point[1] - target[1]) ** 2)
    return distance < threshold

def check_polygon_closure(points, new_point, threshold=0.1):
    if not points:
        return False, [new_point]  # 第一个点
    if len(points) >= 2 and is_near(new_point, points[0], threshold):
        return True, points + [points[0]]  # 闭合多边形
    return False, points + [new_point]

def select_object(x, y):
    global selected_object

    selected_object = None
    
    # 检查是否选中直线
    for i, line in reversed(list(enumerate(lines))):
        if is_point_near_line((x, y), line['points'][0], line['points'][1]):
            selected_object = {'type': 'line', 'index': i}
            return
    
    # 检查是否选中多边形
    for i, polygon in reversed(list(enumerate(polygons))):
        if is_point_in_polygon((x, y), polygon['points']):
            selected_object = {'type': 'polygon', 'index': i}
            return

def is_point_near_line(point, line_start, line_end, threshold=0.05):
    x, y = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # 线段长度
    line_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    if line_length == 0:
        return math.sqrt((x - x1)**2 + (y - y1)**2) < threshold # 直线为一点的情况
    
    # 计算投影比例
    u = ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / (line_length**2)
    
    # 找到线段上最近的点
    if u < 0:
        closest_x, closest_y = x1, y1
    elif u > 1:
        closest_x, closest_y = x2, y2
    else:
        closest_x = x1 + u * (x2 - x1)
        closest_y = y1 + u * (y2 - y1)
    
    # 计算距离
    distance = math.sqrt((x - closest_x)**2 + (y - closest_y)**2)
    return distance < threshold

def is_point_in_polygon(point, polygon):
    # 射线法判断点是否在多边形内
    x, y = point
    inside = False
    n = len(polygon)
    
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

def get_center(points):
    x_sum = sum(p[0] for p in points)
    y_sum = sum(p[1] for p in points)
    return (x_sum / len(points), (y_sum / len(points)))
            
def main():

    if not glfw.init():
        return

    # 设置多重采样（通常 4x MSAA）
    glfw.window_hint(glfw.SAMPLES, 4)

    window = glfw.create_window(window_width, window_height, "卡通动物设计与绘制", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    # 启用多重采样
    glEnable(GL_MULTISAMPLE)

    # glutInit(sys.argv)
    # glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    # glutInitWindowSize(window_width, window_height)
    # glutCreateWindow("卡通动物设计与绘制")
    
    init()
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_cursor_pos_callback(window, cursor_pos_callback)
    glfw.set_key_callback(window, key_callback)
    
    while not glfw.window_should_close(window):
        render(window)
        glfw.poll_events()

    glfw.terminate()

    # 监听事件的绑定
    # glutDisplayFunc(display)
    # glutMouseFunc(click)
    # glutPassiveMotionFunc(move)
    # glutMotionFunc(move)
    # glutKeyboardFunc(keyboard)
    
    # print("使用说明:")
    # print("按 'l' 键: 直线模式")
    # print("按 'p' 键: 多边形模式")
    # print("按 'c' 键: 清除")
    # print("按 ESC 键: 退出")
    # print("\n直线模式: 每次点击确定直线端点")
    # print("多边形模式: 左键添加顶点，右键结束")
    # print("\n颜色选择:")
    # print("1: 黑色  2: 红色  3: 绿色  4: 蓝色")
    # print("5: 黄色  6: 紫色  7: 青色  8: 白色  9: 橙色")
    # print("\n选择模式下:")
    # print("- 点击选择对象（灰色表示选中）")
    # print("- 拖动鼠标移动对象")
    # print("- 方向键缩放对象")
    # print("- 按数字键1-9修改选中对象颜色")
    
    # glutMainLoop()

if __name__ == "__main__":
    main()

