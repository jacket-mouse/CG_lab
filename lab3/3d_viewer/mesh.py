"""
负责3D模型的加载、处理和数据结构管理
"""
import numpy as np

class Mesh:
    def __init__(self):
        self.vertices = []    # 存储顶点坐标 (x,y,z)
        self.faces = []       # 存储面信息 (顶点索引)
        self.normals = []     # 存储顶点法向量
        
    # 为每个顶点计算平滑的法向量，用于光照计算
    def calculate_normals(self):
        self.normals = np.zeros((len(self.vertices), 3), dtype=np.float32)
        
        for face in self.faces:
            if len(face) < 3:
                continue
                
            v0, v1, v2 = [self.vertices[i] for i in face[:3]]
            
            # 计算面法向量（叉积）
            normal = np.cross(v1 - v0, v2 - v0)
            normal = normal / np.linalg.norm(normal) 
            
            for vertex_idx in face:
                self.normals[vertex_idx] += normal
                
        norms = np.linalg.norm(self.normals, axis=1)
        norms[norms == 0] = 1.0  # 避免除0
        self.normals = self.normals / norms[:, np.newaxis]
    
    
    def center_and_scale(self):
        """
        平移变换-将模型包围盒中心对齐坐标系原点
        缩放变换-使模型最大尺寸归一化为1个单位长度
        """
        if self.vertices is None or len(self.vertices) == 0:
            return
        
        # 居中
        vertices = np.array(self.vertices)
        min_coords = np.min(vertices, axis=0)
        max_coords = np.max(vertices, axis=0)
        center = (min_coords + max_coords) / 2.0
        self.vertices = vertices - center
        
        # 缩放
        max_dim = np.max(max_coords - min_coords)
        if max_dim > 0:
            self.vertices /= max_dim
    
    # 加载obj模型
    def load_obj(self, filename):
        self.vertices = []
        self.faces = []
        
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith('v '):
                    parts = line.split()
                    self.vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif line.startswith('f '):
                    parts = line.split()
                    face = []
                    for part in parts[1:]:
                        vertex_info = part.split('/')[0]
                        face.append(int(vertex_info) - 1) # 0-based index
                    self.faces.append(face)
                    
        self.vertices = np.array(self.vertices, dtype=np.float32) # 转换为numpy数组
        self.calculate_normals() 
        self.center_and_scale()


    def load_off(self, filename):
        self.vertices = []
        self.faces = []
        
        with open(filename, 'r') as f:
            line = f.readline().strip()
            if line != "OFF":
                while line == "":
                    line = f.readline().strip()
                if line != "OFF":
                    raise ValueError("Not a valid OFF file")
                    
            line = f.readline().strip()
            while line == "" or line.startswith("#"):
                line = f.readline().strip()
                
            parts = line.split()
            num_vertices = int(parts[0])
            num_faces = int(parts[1])
            
            for _ in range(num_vertices):
                line = f.readline().strip()
                while line == "":
                    line = f.readline().strip()
                parts = line.split()
                self.vertices.append([float(parts[0]), float(parts[1]), float(parts[2])])
                
            for _ in range(num_faces):
                line = f.readline().strip()
                while line == "":
                    line = f.readline().strip()
                parts = line.split()
                num_vertices_in_face = int(parts[0])
                face = [int(parts[i+1]) for i in range(num_vertices_in_face)]
                self.faces.append(face)
                
        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.calculate_normals()
        self.center_and_scale()


    def laplacian_smoothing(self, iterations=1, lambda_factor=0.5):
        """
        Laplacian网格光顺
        :param iterations: 迭代次数
        :param lambda_factor: 平滑系数(0-1)
        """

        if self.vertices.size == 0 or len(self.faces) == 0:
            return
        
        # 构建邻接表
        adjacency = [[] for _ in range(len(self.vertices))]
        for face in self.faces:
            for i in range(len(face)):
                v1 = face[i]
                v2 = face[(i+1)%len(face)]
                if v2 not in adjacency[v1]:
                    adjacency[v1].append(v2)
                if v1 not in adjacency[v2]:
                    adjacency[v2].append(v1)
        
        # 执行光顺迭代
        for _ in range(iterations):
            new_vertices = np.copy(self.vertices)
            for i in range(len(self.vertices)):
                if len(adjacency[i]) == 0:  # 孤立顶点
                    continue
                    
                # 计算Laplacian位移
                neighbor_sum = np.sum(self.vertices[adjacency[i]], axis=0) # fancy indexing
                centroid = neighbor_sum / len(adjacency[i])
                displacement = centroid - self.vertices[i]
                
                # 应用位移
                new_vertices[i] += lambda_factor * displacement
            
            self.vertices = new_vertices
        
        # 更新法向量
        self.calculate_normals()
    