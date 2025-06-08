# 前端开发指南

## 1. 开发环境搭建

### 1.1 安装Node.js
1. 访问 [Node.js官网](https://nodejs.org/)
2. 下载并安装LTS（长期支持）版本
3. 安装完成后，打开命令行工具，验证安装：
```bash
node --version
npm --version
```

### 1.2 安装pnpm
1. 使用npm安装pnpm：
```bash
npm install -g pnpm
```
2. 验证安装：
```bash
pnpm --version
```

### 1.3 安装VSCode
1. 访问 [VSCode官网](https://code.visualstudio.com/)
2. 下载并安装VSCode
3. 安装推荐的VSCode插件：
   - Volar (Vue 3支持)
   - TypeScript Vue Plugin
   - ESLint
   - Prettier
   - GitLens

## 2. 项目结构说明

```
frontend/
├── public/                 # 静态资源目录
├── src/                    # 源代码目录
│   ├── assets/            # 项目资源文件
│   │   ├── common/       # 通用组件
│   │   └── business/     # 业务组件
│   ├── views/            # 页面组件
│   ├── router/           # 路由配置
│   ├── store/            # 状态管理
│   ├── api/              # API接口
│   ├── utils/            # 工具函数
│   ├── styles/           # 样式文件
│   ├── App.vue           # 根组件
│   └── main.ts           # 入口文件
├── index.html            # HTML模板
├── package.json          # 项目配置
├── tsconfig.json         # TypeScript配置
└── vite.config.ts        # Vite配置
```

## 3. 开发流程

### 3.1 启动项目
1. 进入项目目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
pnpm install
```

3. 启动开发服务器：
```bash
pnpm dev
```

4. 在浏览器中访问：http://localhost:5173

### 3.2 修改页面
1. 页面文件位置：`src/views/`
2. 组件文件位置：`src/components/`
3. 样式文件位置：`src/styles/`

### 3.3 添加新页面
1. 在`src/views/`创建新的页面文件
2. 在`src/router/index.ts`中添加路由配置
3. 在`src/components/`中添加需要的组件

### 3.4 修改样式
1. 全局样式：`src/styles/global.css`
2. 组件样式：组件文件中的`<style>`标签
3. 主题配置：`src/styles/theme.css`

## 4. 常用命令

```bash
# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 预览生产版本
pnpm preview

# 运行代码检查
pnpm lint

# 运行单元测试
pnpm test
```

## 5. 开发规范

### 5.1 文件命名
- 组件文件：使用PascalCase（如：`UserProfile.vue`）
- 工具文件：使用camelCase（如：`dateUtils.ts`）
- 样式文件：使用kebab-case（如：`main-header.css`）

### 5.2 代码风格
- 使用TypeScript
- 使用ESLint和Prettier
- 遵循Vue 3组合式API风格
- 使用async/await处理异步

### 5.3 组件开发
- 使用组合式API
- 使用TypeScript类型
- 使用props和emits
- 使用provide/inject

## 6. 调试技巧

### 6.1 浏览器调试
1. 打开浏览器开发者工具（F12）
2. 使用Vue Devtools插件
3. 使用Console面板查看日志
4. 使用Network面板查看请求

### 6.2 代码调试
1. 使用`console.log()`输出调试信息
2. 使用VSCode断点调试
3. 使用Vue Devtools调试组件
4. 使用Chrome DevTools调试

## 7. 常见问题

### 7.1 环境问题
Q: 安装依赖失败怎么办？
A: 检查Node.js版本，清除npm缓存，使用淘宝镜像

Q: 启动项目失败怎么办？
A: 检查端口占用，检查依赖安装，查看错误日志

### 7.2 开发问题
Q: 页面样式不生效怎么办？
A: 检查样式文件引入，检查选择器，检查样式优先级

Q: 组件不显示怎么办？
A: 检查组件注册，检查路由配置，检查组件引入

### 7.3 构建问题
Q: 构建失败怎么办？
A: 检查代码错误，检查依赖版本，检查构建配置

Q: 生产环境问题怎么办？
A: 检查环境变量，检查API配置，检查静态资源

## 8. 学习资源

### 8.1 官方文档
- [Vue 3文档](https://v3.vuejs.org/)
- [TypeScript文档](https://www.typescriptlang.org/)
- [Vite文档](https://vitejs.dev/)
- [Element Plus文档](https://element-plus.org/)

### 8.2 推荐教程
- Vue 3组合式API教程
- TypeScript入门教程
- Vite使用教程
- Element Plus组件教程

### 8.3 工具推荐
- Vue Devtools
- Chrome DevTools
- VSCode插件
- Git工具

## 9. 更新日志

### v1.0.0 (2024-03-xx)
- 初始版本
- 基础功能实现
- 页面框架搭建

### 待开发功能
- 数据可视化
- 主题定制
- 性能优化
- 单元测试 