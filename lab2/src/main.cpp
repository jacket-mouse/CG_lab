#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <iostream>
#include <vector>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#include <algorithm>

const unsigned int SCR_WIDTH = 1600;
const unsigned int SCR_HEIGHT = 1200;

glm::vec3 cameraPos = glm::vec3(1.0f, 1.0f, 1.0f);
glm::vec3 cameraFront = glm::vec3(0.0f, 0.0f, 1.0f);
glm::vec3 cameraUp = glm::vec3(0.0f, 1.0f, 0.0f);

float cameraSpeed = 2.0f;

float yaw = 90.0f;
float pitch = 0.0f;
float lastX = SCR_WIDTH / 2.0f;
float lastY = SCR_HEIGHT / 2.0f;
float fov = 45.0f;
bool firstMouse = true;

float deltaTime = 0.0f;
float lastFrame = 0.0f;

const int MAZE_WIDTH = 10;
const int MAZE_HEIGHT = 10;
bool maze[MAZE_WIDTH][MAZE_HEIGHT] = {
    {1, 1, 1, 1, 1, 1, 1, 1, 1, 1}, // 列0
    {1, 0, 0, 0, 0, 0, 0, 0, 0, 1}, // 列1
    {1, 1, 1, 1, 1, 1, 1, 1, 0, 1}, // 列2
    {1, 0, 0, 0, 0, 0, 0, 0, 0, 1}, // 列3
    {1, 0, 1, 1, 0, 1, 1, 1, 0, 1}, // 列4
    {1, 0, 1, 1, 0, 0, 1, 0, 0, 1}, // 列5
    {1, 0, 0, 0, 1, 0, 1, 0, 1, 1}, // 列6
    {1, 1, 1, 1, 1, 0, 1, 1, 1, 1}, // 列7
    {1, 0, 0, 0, 0, 0, 0, 0, 0, 1}, // 列8
    {1, 1, 1, 1, 1, 1, 1, 1, 1, 1}  // 列9
};

// 跳跃相关变量
bool isJumping = false;
float jumpVelocity = 0.0f;
const float gravity = -9.8f;            // 重力加速度
const float initialJumpVelocity = 5.0f; // 初始跳跃速度

bool gameOver = false;
glm::vec3 redCubePos(3.0f, 1.0f, 5.0f); // 红色方块初始位置
const float cubeSize = 0.5f;            // 方块大小

// 碰撞参数
const float CAMERA_RADIUS = 0.15f; // 摄像机的碰撞半径

unsigned int floorTexture, wallTexture;

const char *vertexShaderSource = R"(
    #version 330 core
    layout (location = 0) in vec3 aPos;
    layout (location = 1) in vec2 aTexCoord;
    out vec2 TexCoord;
    uniform mat4 model;
    uniform mat4 view;
    uniform mat4 projection;
    void main()
    {
        gl_Position = projection * view * model * vec4(aPos, 1.0);
        TexCoord = aTexCoord;
    }
)";

const char *fragmentShaderSource = R"(
    #version 330 core
    out vec4 FragColor;
    in vec2 TexCoord;
    uniform sampler2D texture1;
    void main()
    {
        FragColor = texture(texture1, TexCoord);
    }
)";

unsigned int loadTexture(const char *path, bool generateMipmaps = true, GLint minFilter = GL_LINEAR_MIPMAP_LINEAR, GLint magFilter = GL_LINEAR)
{
    unsigned int textureID;
    // 为当前绑定的纹理对象设置环绕、过滤方式
    glGenTextures(1, &textureID);
    glBindTexture(GL_TEXTURE_2D, textureID);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

    // 加载并生成纹理
    int width, height, nrComponents;
    unsigned char *data = stbi_load(path, &width, &height, &nrComponents, 0);
    if (data)
    {
        GLenum format;
        if (nrComponents == 1)
            format = GL_RED;
        else if (nrComponents == 3)
            format = GL_RGB;
        else if (nrComponents == 4)
            format = GL_RGBA;
        // 纹理对象被附上纹理图像
        glTexImage2D(GL_TEXTURE_2D, 0, format, width, height, 0, format, GL_UNSIGNED_BYTE, data);
        glGenerateMipmap(GL_TEXTURE_2D);
        stbi_image_free(data);
    }
    else
    {
        std::cout << "Texture failed to load at path: " << path << std::endl;
        stbi_image_free(data);
    }

    return textureID;
}

bool checkWallCollision(const glm::vec3 &cameraPos)
{

    // if (cameraPos.x < 0.65f || cameraPos.x > MAZE_WIDTH - 1.65f || cameraPos.z < 0.65f || cameraPos.z > MAZE_HEIGHT - 1.65f)
    // {
    //     return true;
    // }
    const int centerX = static_cast<int>(std::round(cameraPos.x));
    const int centerZ = static_cast<int>(std::round(cameraPos.z));

    for (int i = std::max(0, centerX - 1); i <= std::min(MAZE_WIDTH - 1, centerX + 1); ++i)
    {
        for (int j = std::max(0, centerZ - 1); j <= std::min(MAZE_HEIGHT - 1, centerZ + 1); ++j)
        {
            if (maze[i][j] == 1)
            {

                const glm::vec3 wallMin(i - 0.5f, 1.0f, j - 0.5f);
                const glm::vec3 wallMax(i + 0.5f, 1.0f, j + 0.5f);

                // camera抽象成了方块
                const glm::vec3 cameraMin = cameraPos - glm::vec3(CAMERA_RADIUS);
                const glm::vec3 cameraMax = cameraPos + glm::vec3(CAMERA_RADIUS);

                // AABB碰撞检测
                if (cameraMax.x > wallMin.x && cameraMin.x < wallMax.x &&
                    cameraMax.z > wallMin.z && cameraMin.z < wallMax.z)
                {
                    std::cout << "Camera collided with wall at (" << i << ", " << j << ")" << std::endl;
                    return true;
                }
            }
        }
    }
    return false;
}

void processInput(GLFWwindow *window)
{
    if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS)
        glfwSetWindowShouldClose(window, true);

    float currentFrame = glfwGetTime();
    deltaTime = currentFrame - lastFrame;
    lastFrame = currentFrame;

    float velocity = cameraSpeed * deltaTime;

    glm::vec3 oldPos = cameraPos; // 记录旧位置

    // 更平滑的移动控制
    if (glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS)
        cameraPos += velocity * glm::normalize(glm::vec3(cameraFront.x, 0.0f, cameraFront.z));
    if (glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS)
        cameraPos -= velocity * glm::normalize(glm::vec3(cameraFront.x, 0.0f, cameraFront.z));
    if (glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS)
        cameraPos -= glm::normalize(glm::cross(cameraFront, cameraUp)) * velocity;
    if (glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS)
        cameraPos += glm::normalize(glm::cross(cameraFront, cameraUp)) * velocity;

    // 碰撞检测
    if (checkWallCollision(cameraPos))
    {
        cameraPos = oldPos; // 恢复到旧位置
    }

    // 空格键触发跳跃
    if (glfwGetKey(window, GLFW_KEY_SPACE) == GLFW_PRESS && !isJumping)
    {
        isJumping = true;
        jumpVelocity = initialJumpVelocity;
    }
}

void mouse_callback(GLFWwindow *window, double xpos, double ypos)
{
    float mouseSensitivity = 0.05f;
    if (firstMouse)
    {
        lastX = xpos;
        lastY = ypos;
        firstMouse = false;
    }

    float xoffset = xpos - lastX;
    float yoffset = lastY - ypos; // 反转Y轴
    lastX = xpos;
    lastY = ypos;

    xoffset *= mouseSensitivity;
    yoffset *= mouseSensitivity;

    yaw += xoffset;
    pitch += yoffset;

    // 限制俯仰角
    pitch = std::max(-89.0f, std::min(89.0f, pitch));

    // 计算新的前向向量
    glm::vec3 front;
    front.x = cos(glm::radians(yaw)) * cos(glm::radians(pitch));
    front.y = sin(glm::radians(pitch));
    front.z = sin(glm::radians(yaw)) * cos(glm::radians(pitch));
    cameraFront = glm::normalize(front);
}

void scroll_callback(GLFWwindow *window, double xoffset, double yoffset)
{
    if (fov >= 1.0f && fov <= 45.0f)
        fov -= yoffset;
    if (fov <= 1.0f)
        fov = 1.0f;
    if (fov >= 45.0f)
        fov = 45.0f;
}

unsigned int createCubeVAO()
{
    float vertices[] = {
        // 背面
        -0.5f, -0.5f, -0.5f, 0.0f, 0.0f,
        0.5f, -0.5f, -0.5f, 1.0f, 0.0f,
        0.5f, 0.5f, -0.5f, 1.0f, 1.0f,
        0.5f, 0.5f, -0.5f, 1.0f, 1.0f,
        -0.5f, 0.5f, -0.5f, 0.0f, 1.0f,
        -0.5f, -0.5f, -0.5f, 0.0f, 0.0f,

        // 前面
        -0.5f, -0.5f, 0.5f, 0.0f, 0.0f,
        0.5f, -0.5f, 0.5f, 1.0f, 0.0f,
        0.5f, 0.5f, 0.5f, 1.0f, 1.0f,
        0.5f, 0.5f, 0.5f, 1.0f, 1.0f,
        -0.5f, 0.5f, 0.5f, 0.0f, 1.0f,
        -0.5f, -0.5f, 0.5f, 0.0f, 0.0f,

        // 左面
        -0.5f, 0.5f, 0.5f, 1.0f, 0.0f,
        -0.5f, 0.5f, -0.5f, 1.0f, 1.0f,
        -0.5f, -0.5f, -0.5f, 0.0f, 1.0f,
        -0.5f, -0.5f, -0.5f, 0.0f, 1.0f,
        -0.5f, -0.5f, 0.5f, 0.0f, 0.0f,
        -0.5f, 0.5f, 0.5f, 1.0f, 0.0f,

        // 右面
        0.5f, 0.5f, 0.5f, 1.0f, 0.0f,
        0.5f, 0.5f, -0.5f, 1.0f, 1.0f,
        0.5f, -0.5f, -0.5f, 0.0f, 1.0f,
        0.5f, -0.5f, -0.5f, 0.0f, 1.0f,
        0.5f, -0.5f, 0.5f, 0.0f, 0.0f,
        0.5f, 0.5f, 0.5f, 1.0f, 0.0f,

        // 下面
        -0.5f, -0.5f, -0.5f, 0.0f, 1.0f,
        0.5f, -0.5f, -0.5f, 1.0f, 1.0f,
        0.5f, -0.5f, 0.5f, 1.0f, 0.0f,
        0.5f, -0.5f, 0.5f, 1.0f, 0.0f,
        -0.5f, -0.5f, 0.5f, 0.0f, 0.0f,
        -0.5f, -0.5f, -0.5f, 0.0f, 1.0f,

        // 上面
        -0.5f, 0.5f, -0.5f, 0.0f, 1.0f,
        0.5f, 0.5f, -0.5f, 1.0f, 1.0f,
        0.5f, 0.5f, 0.5f, 1.0f, 0.0f,
        0.5f, 0.5f, 0.5f, 1.0f, 0.0f,
        -0.5f, 0.5f, 0.5f, 0.0f, 0.0f,
        -0.5f, 0.5f, -0.5f, 0.0f, 1.0f};

    unsigned int VBO, VAO;
    glGenVertexArrays(1, &VAO);
    glGenBuffers(1, &VBO);

    glBindVertexArray(VAO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);

    // 位置属性
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void *)0);
    glEnableVertexAttribArray(0);
    // 纹理坐标属性
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void *)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);

    return VAO;
}

int main()
{
    glfwInit();
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    GLFWwindow *window = glfwCreateWindow(SCR_WIDTH, SCR_HEIGHT, "3D迷宫游戏", NULL, NULL);
    if (window == NULL)
    {
        std::cout << "Failed to create GLFW window" << std::endl;
        glfwTerminate();
        return -1;
    }
    glfwMakeContextCurrent(window);
    glfwSetCursorPosCallback(window, mouse_callback);
    glfwSetScrollCallback(window, scroll_callback);
    glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED); // 隐藏光标并锁定在窗口中

    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress))
    {
        std::cout << "Failed to initialize GLAD" << std::endl;
        return -1;
    }

    glEnable(GL_DEPTH_TEST);

    unsigned int vertexShader = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vertexShader, 1, &vertexShaderSource, NULL);
    glCompileShader(vertexShader);

    unsigned int fragmentShader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fragmentShader, 1, &fragmentShaderSource, NULL);
    glCompileShader(fragmentShader);

    unsigned int shaderProgram = glCreateProgram();
    glAttachShader(shaderProgram, vertexShader);
    glAttachShader(shaderProgram, fragmentShader);
    glLinkProgram(shaderProgram);

    glDeleteShader(vertexShader);
    glDeleteShader(fragmentShader);

    unsigned int cubeVAO = createCubeVAO();

    floorTexture = loadTexture("D:\\Project\\CG_lab\\lab2\\src\\resources\\textures\\Tile2.jpg", true, GL_LINEAR_MIPMAP_LINEAR, GL_LINEAR);
    wallTexture = loadTexture("D:\\Project\\CG_lab\\lab2\\src\\resources\\textures\\Tiles132A.jpg", true, GL_LINEAR_MIPMAP_LINEAR, GL_LINEAR);
    if (!floorTexture || !wallTexture)
    {
        std::cout << "Failed to load textures!" << std::endl;
        return -1;
    }
    // 渲染循环
    while (!glfwWindowShouldClose(window))
    {
        processInput(window);

        // 更新跳跃状态
        if (isJumping)
        {
            cameraPos.y += jumpVelocity * deltaTime;
            jumpVelocity += gravity * deltaTime;

            // 检查是否落地
            if (cameraPos.y <= 1.0f)
            {
                cameraPos.y = 1.0f;
                isJumping = false;
                jumpVelocity = 0.0f;
            }
        }

        // 更新红色方块位置
        float timeValue = glfwGetTime();
        redCubePos.z = 5.0f + 3.5f * sin(timeValue);

        // 碰撞检测
        if (!gameOver)
        {
            glm::vec3 cameraToCube = cameraPos - redCubePos;
            float distance = glm::length(cameraToCube);

            // 简单球形碰撞检测
            if (distance < (cubeSize + 0.5f))
            {
                cameraPos = glm::vec3(1.0f, 1.0f, 1.0f);   // 重置摄像机位置
                cameraFront = glm::vec3(0.0f, 0.0f, 1.0f); // 重置摄像机朝向
                yaw = 90.0f;                               // 重置摄像机偏航角
                pitch = 0.0f;                              // 重置摄像机俯仰角
            }
        }

        glClearColor(0.2f, 0.3f, 0.3f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        glUseProgram(shaderProgram);

        glm::mat4 view = glm::lookAt(cameraPos, cameraPos + cameraFront, cameraUp);
        glm::mat4 projection = glm::perspective(glm::radians(fov), (float)SCR_WIDTH / (float)SCR_HEIGHT, 0.1f, 100.0f);

        glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "view"), 1, GL_FALSE, glm::value_ptr(view));
        glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "projection"), 1, GL_FALSE, glm::value_ptr(projection));

        // 绘制地板
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, floorTexture);
        glUniform1i(glGetUniformLocation(shaderProgram, "texture1"), 0);

        glm::mat4 model = glm::mat4(1.0f);
        model = glm::translate(model, glm::vec3(MAZE_WIDTH / 2.0f - 0.5f, -0.5f, MAZE_HEIGHT / 2.0f - 0.5f));
        model = glm::scale(model, glm::vec3(MAZE_WIDTH, 0.1f, MAZE_HEIGHT));
        glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "model"), 1, GL_FALSE, glm::value_ptr(model));

        glBindVertexArray(cubeVAO);
        glDrawArrays(GL_TRIANGLES, 0, 36);

        // 绘制墙壁
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, wallTexture);
        glUniform1i(glGetUniformLocation(shaderProgram, "texture1"), 0);

        for (int i = 0; i < MAZE_WIDTH; ++i)
        {
            for (int j = 0; j < MAZE_HEIGHT; ++j)
            {
                if (maze[i][j])
                {
                    model = glm::mat4(1.0f);
                    model = glm::translate(model, glm::vec3(i, 0.5f, j));
                    model = glm::scale(model, glm::vec3(1.0f, 2.0f, 1.0f));
                    glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "model"), 1, GL_FALSE, glm::value_ptr(model));
                    glDrawArrays(GL_TRIANGLES, 0, 36);
                }
            }
        }

        // 绘制终点（绿色方块）
        const char *fragmentShaderSourceNoTexture = R"(
            #version 330 core
            out vec4 FragColor;
            void main() {
                FragColor = vec4(0.0f, 1.0f, 0.0f, 1.0f);
            }
        )";

        unsigned int fragmentShaderNoTexture = glCreateShader(GL_FRAGMENT_SHADER);
        glShaderSource(fragmentShaderNoTexture, 1, &fragmentShaderSourceNoTexture, NULL);
        glCompileShader(fragmentShaderNoTexture);

        unsigned int shaderProgramNoTexture = glCreateProgram();
        glAttachShader(shaderProgramNoTexture, vertexShader);
        glAttachShader(shaderProgramNoTexture, fragmentShaderNoTexture);
        glLinkProgram(shaderProgramNoTexture);

        glUseProgram(shaderProgramNoTexture);
        glUniformMatrix4fv(glGetUniformLocation(shaderProgramNoTexture, "view"), 1, GL_FALSE, glm::value_ptr(view));
        glUniformMatrix4fv(glGetUniformLocation(shaderProgramNoTexture, "projection"), 1, GL_FALSE, glm::value_ptr(projection));

        model = glm::mat4(1.0f);
        model = glm::translate(model, glm::vec3(MAZE_WIDTH - 2, 0.5f, MAZE_HEIGHT - 2));
        model = glm::scale(model, glm::vec3(0.5f, 0.5f, 0.5f));
        glUniformMatrix4fv(glGetUniformLocation(shaderProgramNoTexture, "model"), 1, GL_FALSE, glm::value_ptr(model));
        glDrawArrays(GL_TRIANGLES, 0, 36);

        // 绘制移动的红色方块（使用时间函数）
        const char *fragmentShaderSourceRed = R"(
            #version 330 core
            out vec4 FragColor;
            void main() {
                FragColor = vec4(1.0f, 0.0f, 0.0f, 1.0f);
            }
        )";

        unsigned int fragmentShaderRed = glCreateShader(GL_FRAGMENT_SHADER);
        glShaderSource(fragmentShaderRed, 1, &fragmentShaderSourceRed, NULL);
        glCompileShader(fragmentShaderRed);

        unsigned int shaderProgramRed = glCreateProgram();
        glAttachShader(shaderProgramRed, vertexShader);
        glAttachShader(shaderProgramRed, fragmentShaderRed);
        glLinkProgram(shaderProgramRed);

        glUseProgram(shaderProgramRed);
        glUniformMatrix4fv(glGetUniformLocation(shaderProgramRed, "view"), 1, GL_FALSE, glm::value_ptr(view));
        glUniformMatrix4fv(glGetUniformLocation(shaderProgramRed, "projection"), 1, GL_FALSE, glm::value_ptr(projection));

        float zPos = 5.0f + 3.0f * sin(timeValue);

        model = glm::mat4(1.0f);
        model = glm::translate(model, glm::vec3(3.0f, 0.1f, zPos));
        model = glm::scale(model, glm::vec3(0.5f, 0.4f, 0.5f));
        glUniformMatrix4fv(glGetUniformLocation(shaderProgramRed, "model"), 1, GL_FALSE, glm::value_ptr(model));
        glDrawArrays(GL_TRIANGLES, 0, 36);

        glDeleteShader(fragmentShaderNoTexture);
        glDeleteProgram(shaderProgramNoTexture);

        // 检查是否到达终点
        if (cameraPos.x >= MAZE_WIDTH - 2 && cameraPos.z >= MAZE_HEIGHT - 2)
        {
            std::cout << "Congratulations! You reached the end of the maze!" << std::endl;
            glfwSetWindowShouldClose(window, true);
        }

        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    // 清理资源
    glDeleteVertexArrays(1, &cubeVAO);
    glDeleteProgram(shaderProgram);
    glDeleteTextures(1, &floorTexture);
    glDeleteTextures(1, &wallTexture);

    glfwTerminate();
    return 0;
}