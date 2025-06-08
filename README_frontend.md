# 数据分析平台前端项目

## 项目说明
这是一个基于Vue 3的数据分析平台前端项目，使用Vite作为构建工具。

## 技术栈
- Vue 3
- Element Plus
- Vue Router
- Pinia
- Axios

## 开发环境要求
- Node.js >= 16.0.0
- npm >= 7.0.0

## 项目结构
```
frontend/
├── src/                # 源代码目录
│   ├── assets/        # 静态资源
│   ├── components/    # 公共组件
│   ├── views/         # 页面组件
│   ├── router/        # 路由配置
│   ├── store/         # 状态管理
│   ├── api/           # API接口
│   ├── utils/         # 工具函数
│   ├── App.vue        # 根组件
│   └── main.js        # 入口文件
├── public/            # 公共资源
└── index.html         # HTML模板
```

## 快速开始

### 安装依赖
```bash
cd frontend
npm install
```

### 启动开发服务器
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

## 开发指南

### 1. 组件开发规范
- 组件文件使用PascalCase命名
- 组件名应该始终是多个单词的
- 组件文件应该放在对应的目录下

### 2. 路由配置
- 路由配置文件位于 `src/router/index.js`
- 新增页面需要在路由配置中添加对应路由

### 3. 状态管理
- 使用Pinia进行状态管理
- 状态模块位于 `src/store` 目录

### 4. API调用
- API接口统一管理在 `src/api` 目录
- 使用Axios进行HTTP请求

## 常见问题
1. 如果遇到依赖安装问题，可以尝试删除 `node_modules` 目录后重新安装
2. 开发时请确保后端API服务已启动

## 更新日志
- 2024-03-07: 项目初始化 
