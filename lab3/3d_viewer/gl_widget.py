"""
OpenGL渲染和交互
"""

from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtOpenGL import QGLWidget, QGLFormat
from PyQt5.QtCore import Qt, QSize, QTimer
from mesh import Mesh

class GLWidget(QGLWidget):
    def __init__(self, parent=None):
        fmt = QGLFormat()
        fmt.setStereo(True) # 启用立体缓冲
        super(GLWidget, self).__init__(fmt, parent)
        self.mesh = Mesh()
        self.xRot = self.yRot = self.zRot = 0  # 旋转角度
        self.zoom = 1.0
        self.translation = [0.0, 0.0, -5.0]
        self.lastPos = None
        self.wireframe = False
        self.lighting = True
        
        # 光照参数初始化 RGB + alpha
        self.light_params = {
            'ambient': [0.2, 0.2, 0.2, 1.0],
            'diffuse': [0.8, 0.8, 0.8, 1.0],
            'specular': [1.0, 1.0, 1.0, 1.0],
            'position': [1.0, 1.0, 1.0, 0.0],
            'shininess': 100.0,
            'enabled': True
        }
        
        # 材质参数
        self.material = {
            'ambient': [0.2, 0.2, 0.2, 1.0],
            'diffuse': [0.8, 0.8, 0.8, 1.0],
            'specular': [0.5, 0.5, 0.5, 1.0],
            'emission': [0.0, 0.0, 0.0, 1.0]
        }

        self.smoothing_iterations = 0
        self.max_iterations = 20
        self.smoothing_timer = QTimer(self)
        self.smoothing_timer.timeout.connect(self.step_smoothing)
        self.lambda_factor = 0.3  # 默认平滑系数
        
    def minimumSizeHint(self):
        return QSize(400, 400)
        
    def sizeHint(self):
        return QSize(800, 600)
        
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.render()
        
    def render(self):
        # 应用模型变换
        glTranslatef(*self.translation)
        glRotatef(self.xRot / 16.0, 1.0, 0.0, 0.0)
        glRotatef(self.yRot / 16.0, 0.0, 1.0, 0.0)
        glRotatef(self.zRot / 16.0, 0.0, 0.0, 1.0)
        glScalef(self.zoom, self.zoom, self.zoom)
        
        if self.lighting:
            glEnable(GL_LIGHTING)
        else:
            glDisable(GL_LIGHTING)
            
        if self.wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glDisable(GL_LIGHTING)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            
        self.draw_mesh()
          
    def draw_mesh(self):
        if self.mesh.vertices is None or len(self.mesh.vertices) == 0:
            return
        
            
        glBegin(GL_TRIANGLES)
        for face in self.mesh.faces:
            if len(face) < 3:
                continue
                
            # 三角形面
            if len(face) == 3:
                for vertex_idx in face:
                    glNormal3fv(self.mesh.normals[vertex_idx])
                    glVertex3fv(self.mesh.vertices[vertex_idx])
            # 多边形面
            else:
                for i in range(1, len(face) - 1):
                    # 绘制三角形扇
                    glNormal3fv(self.mesh.normals[face[0]])
                    glVertex3fv(self.mesh.vertices[face[0]])
                    glNormal3fv(self.mesh.normals[face[i]])
                    glVertex3fv(self.mesh.vertices[face[i]])
                    glNormal3fv(self.mesh.normals[face[i+1]])
                    glVertex3fv(self.mesh.vertices[face[i+1]])
        glEnd()
        
    def resizeGL(self, width, height):
        side = min(width, height)
        glViewport((width - side) // 2, (height - side) // 2, side, side)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / float(height) if height != 0 else 1.0
        gluPerspective(45.0, aspect, 0.1, 100.0)
        
    def mousePressEvent(self, event):
        self.lastPos = event.pos()
        
    def mouseMoveEvent(self, event):
        if self.lastPos is None:
            return
            
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()
        
        if event.buttons() & Qt.LeftButton:
            self.yRot += dx # 左右旋转
            self.xRot += dy # 上下旋转
        elif event.buttons() & Qt.RightButton:
            self.translation[0] += dx * 0.01
            self.translation[1] -= dy * 0.01
            
        self.lastPos = event.pos()
        self.update()
        
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom *= 1.1
        elif delta < 0:
            self.zoom /= 1.1
        self.update()
    
    # 加载网格文件
    def load_mesh(self, filename):
        if filename.lower().endswith('.obj'):
            self.mesh.load_obj(filename)
        elif filename.lower().endswith('.off'):
            self.mesh.load_off(filename)
        else:
            raise ValueError("Unsupported file format")
            
        self.update()
        
    # 网格显示模式切换
    def toggle_wireframe(self):
        self.wireframe = not self.wireframe
        self.update()
        
    def stereo_format(self):
        fmt = self.format()
        fmt.setStereo(True)
        return fmt
    
    def step_smoothing(self):
        if self.smoothing_iterations < self.max_iterations:
            try:
                self.mesh.laplacian_smoothing(iterations=1, lambda_factor=self.lambda_factor)
                self.smoothing_iterations += 1
                
                main_window = self.parent().parent()  # QGLWidget -> CentralWidget -> MainWindow
                if hasattr(main_window, 'update_iteration_label'):
                    main_window.update_iteration_label(self.smoothing_iterations)
                    
                self.update()
            except Exception as e:
                print(f"Smoothing error: {e}")
                self.smoothing_timer.stop()
        else:
            self.smoothing_timer.stop()
    
    def start_smoothing_animation(self, max_iter=20, lambda_factor=0.3):
        self.max_iterations = max_iter
        self.lambda_factor = lambda_factor
        self.smoothing_iterations = 0
        self.smoothing_timer.start(200)  # 每200ms更新一次

    def initializeGL(self):
        """
        第一次显示窗口时
        窗口大小改变时
        OpenGL 上下文需要重新初始化时
        """
        glClearColor(0.1, 0.1, 0.2, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glShadeModel(GL_SMOOTH)
        
        # 设置光照
        self.setup_lighting()
        
    def setup_lighting(self):
        if self.light_params['enabled']:
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            
            # 光源属性
            glLightfv(GL_LIGHT0, GL_AMBIENT, self.light_params['ambient'])
            glLightfv(GL_LIGHT0, GL_DIFFUSE, self.light_params['diffuse'])
            glLightfv(GL_LIGHT0, GL_SPECULAR, self.light_params['specular'])
            glLightfv(GL_LIGHT0, GL_POSITION, self.light_params['position'])
            
            # 设置材质属性
            glMaterialfv(GL_FRONT, GL_AMBIENT, self.material['ambient'])
            glMaterialfv(GL_FRONT, GL_DIFFUSE, self.material['diffuse'])
            glMaterialfv(GL_FRONT, GL_SPECULAR, self.material['specular'])
            glMaterialfv(GL_FRONT, GL_EMISSION, self.material['emission'])
            glMaterialfv(GL_FRONT, GL_SHININESS, self.light_params['shininess'])
        else:
            glDisable(GL_LIGHTING)