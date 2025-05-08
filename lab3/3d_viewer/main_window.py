"""
负责UI界面和程序流程控制
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QFileDialog, 
                           QLabel, QSlider, QGroupBox, QCheckBox,
                           QFormLayout)
from PyQt5.QtCore import Qt
from gl_widget import GLWidget
import os

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Model Viewer")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout() # 垂直布局
        central_widget.setLayout(main_layout)
        
        self.glWidget = GLWidget(central_widget) # 创建OpenGL窗口
        main_layout.addWidget(self.glWidget)
        
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)
        main_layout.addWidget(control_panel)
        
        self.load_button = QPushButton("加载模型")
        self.load_button.clicked.connect(self.load_model)
        control_layout.addWidget(self.load_button)
        
        self.wireframe_button = QPushButton("显示网格")
        self.wireframe_button.clicked.connect(self.glWidget.toggle_wireframe)
        control_layout.addWidget(self.wireframe_button)
        
        # 添加平滑控制组件
        smoothing_group = QGroupBox("Laplacian Smoothing")
        smoothing_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Smoothing")
        self.start_button.clicked.connect(self.start_smoothing)
        smoothing_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_smoothing)
        smoothing_layout.addWidget(self.stop_button)
        
        self.iter_slider = QSlider(Qt.Horizontal)
        self.iter_slider.setRange(1, 50)
        self.iter_slider.setValue(20)
        smoothing_layout.addWidget(QLabel("Iterations:"))
        smoothing_layout.addWidget(self.iter_slider)
        
        self.lambda_slider = QSlider(Qt.Horizontal)
        self.lambda_slider.setRange(1, 9)
        self.lambda_slider.setValue(3)
        smoothing_layout.addWidget(QLabel("Lambda:"))
        smoothing_layout.addWidget(self.lambda_slider)
        
        self.iteration_label = QLabel("Iteration: 0/20")
        smoothing_layout.addWidget(self.iteration_label)
        
        smoothing_group.setLayout(smoothing_layout)
        main_layout.addWidget(smoothing_group)
        
        # 添加光照控制面板
        light_group = QGroupBox("Lighting Controls")
        light_layout = QVBoxLayout()
        
        # 光照开关
        self.light_toggle = QCheckBox("Enable Lighting")
        self.light_toggle.setChecked(True)
        self.light_toggle.stateChanged.connect(self.toggle_lighting)
        light_layout.addWidget(self.light_toggle)
        
        # 光源位置控制
        pos_group = QGroupBox("Light Position")
        pos_layout = QHBoxLayout()
        
        self.x_slider = self.create_slider(-5, 5, 1, self.update_light_position)
        self.y_slider = self.create_slider(-5, 5, 1, self.update_light_position)
        self.z_slider = self.create_slider(-5, 5, -1, self.update_light_position)
        
        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(self.x_slider)
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(self.y_slider)
        pos_layout.addWidget(QLabel("Z:"))
        pos_layout.addWidget(self.z_slider)
        pos_group.setLayout(pos_layout)
        light_layout.addWidget(pos_group)
        
        # 光照参数控制
        param_group = QGroupBox("Light Parameters")
        param_layout = QFormLayout()
        
        self.ambient_slider = self.create_color_slider(20, self.update_light_ambient)
        self.diffuse_slider = self.create_color_slider(80, self.update_light_diffuse)
        self.specular_slider = self.create_color_slider(100, self.update_light_specular)
        
        """
        Ambient 控制环境光强度 基础亮度
        Diffuse 控制漫反射强度 主要光照
        Specular 控制高光强度
        """
        param_layout.addRow("Ambient:", self.ambient_slider)
        param_layout.addRow("Diffuse:", self.diffuse_slider)
        param_layout.addRow("Specular:", self.specular_slider)
        param_group.setLayout(param_layout)
        light_layout.addWidget(param_group)
        
        light_group.setLayout(light_layout)
        main_layout.addWidget(light_group)

        self.statusBar().showMessage("Ready")
        
    def load_model(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open 3D Model", "", "3D Model Files (*.obj *.off)")
            
        if filename:
            try:
                self.glWidget.load_mesh(filename)
                self.statusBar().showMessage(f"Loaded: {os.path.basename(filename)}")
            except Exception as e:
                self.statusBar().showMessage(f"Error: {str(e)}")
                print(str(e))

    def start_smoothing(self):
        max_iter = self.iter_slider.value()
        lambda_factor = self.lambda_slider.value() / 10.0
        self.glWidget.start_smoothing_animation(max_iter, lambda_factor)
    
    def stop_smoothing(self):
        self.glWidget.smoothing_timer.stop()
    
    def update_iteration_label(self, current_iter):
        max_iter = self.iter_slider.value()
        self.iteration_label.setText(f"Iteration: {current_iter}/{max_iter}")

    def create_slider(self, min_val, max_val, init_val, callback):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val * 10, max_val * 10)
        slider.setValue(init_val * 10)
        slider.valueChanged.connect(callback)
        return slider
        
    def create_color_slider(self, init_val, callback):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(init_val)
        slider.valueChanged.connect(callback)
        return slider
        
    def toggle_lighting(self, state):
        self.glWidget.light_params['enabled'] = state == Qt.Checked
        self.glWidget.setup_lighting()
        self.glWidget.update()
        
    def update_light_position(self):
        x = self.x_slider.value() / 10.0
        y = self.y_slider.value() / 10.0
        z = self.z_slider.value() / 10.0
        self.glWidget.light_params['position'] = [x, y, z, 0.0]
        self.glWidget.setup_lighting()
        self.glWidget.update()
        
    def update_light_ambient(self, value):
        val = value / 100.0
        self.glWidget.light_params['ambient'] = [val, val, val, 1.0]
        self.glWidget.setup_lighting()
        self.glWidget.update()
        
    def update_light_diffuse(self, value):
        val = value / 100.0
        self.glWidget.light_params['diffuse'] = [val, val, val, 1.0]
        self.glWidget.setup_lighting()
        self.glWidget.update()
        
    def update_light_specular(self, value):
        val = value / 100.0
        self.glWidget.light_params['specular'] = [val, val, val, 1.0]
        self.glWidget.setup_lighting()
        self.glWidget.update()
        