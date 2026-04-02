# IPAM System - 开发者指南

本指南面向希望参与 IPAM 系统开发或进行二次开发的开发者。

## 目录

1. [开发环境搭建](#开发环境搭建)
2. [项目结构](#项目结构)
3. [后端开发](#后端开发)
4. [前端开发](#前端开发)
5. [数据库管理](#数据库管理)
6. [测试](#测试)
7. [代码规范](#代码规范)
8. [调试技巧](#调试技巧)

## 开发环境搭建

### 本地开发（不使用 Docker）

#### 后端开发环境

1. **安装 Python 3.10+**
   ```bash
   python --version  # 确认版本
   ```

2. **创建虚拟环境**
   ```bash
   cd backend
   python -m venv venv
   
   # 激活虚拟环境
   # Windows
   venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，修改 MYSQL_HOST=localhost
   ```

5. **启动本地 MySQL**
   ```bash
   # 使用 Docker 启动 MySQL
   docker run -d \
     --name ipam-mysql-dev \
     -e MYSQL_ROOT_PASSWORD=root_password \
     -e MYSQL_DATABASE=ipam_db \
     -e MYSQL_USER=ipam \
     -e MYSQL_PASSWORD=ipam_password \
     -p 3306:3306 \
     mysql:8.0
   ```

6. **运行开发服务器**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### 前端开发环境

1. **安装 Node.js 18+**
   ```bash
   node --version  # 确认版本
   npm --version
   ```

2. **安装依赖**
   ```bash
   cd frontend
   npm install
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件
   ```

4. **运行开发服务器**
   ```bash
   npm run dev
   ```

### 使用 Docker 开发

推荐使用 Docker Compose 进行开发，支持热重载：

```bash
# 启动所有服务
docker-compose up

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 项目结构

### 后端结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── api/                 # API 路由
│   │   ├── __init__.py
│   │   ├── deps.py         # 依赖注入
│   │   ├── auth.py         # 认证路由
│   │   ├── users.py        # 用户管理路由
│   │   ├── network_segments.py
│   │   ├── ip_addresses.py
│   │   ├── devices.py
│   │   ├── logs.py
│   │   ├── dashboard.py
│   │   └── import_export.py
│   ├── core/                # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py       # 配置管理
│   │   ├── security.py     # 安全相关（JWT、密码）
│   │   └── database.py     # 数据库连接
│   ├── models/              # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── network_segment.py
│   │   ├── ip_address.py
│   │   ├── device.py
│   │   ├── operation_log.py
│   │   └── alert.py
│   ├── schemas/             # Pydantic 模式
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── network_segment.py
│   │   ├── ip_address.py
│   │   ├── device.py
│   │   └── common.py
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── ip_service.py
│   │   ├── device_service.py
│   │   ├── conflict_detection.py
│   │   ├── ping_scanner.py
│   │   ├── alert_service.py
│   │   └── excel_service.py
│   └── utils/               # 工具函数
│       ├── __init__.py
│       ├── ip_utils.py
│       ├── validators.py
│       └── logger.py
├── alembic/                 # 数据库迁移
├── tests/                   # 测试文件
├── logs/                    # 日志文件
├── .env                     # 环境变量
├── .env.example
├── requirements.txt
└── Dockerfile
```

### 前端结构

```
frontend/
├── src/
│   ├── main.js              # 应用入口
│   ├── App.vue              # 根组件
│   ├── api/                 # API 请求
│   │   ├── request.js      # Axios 配置
│   │   ├── auth.js
│   │   ├── network.js
│   │   ├── ip.js
│   │   ├── device.js
│   │   └── dashboard.js
│   ├── components/          # 可复用组件
│   │   ├── Layout/
│   │   │   ├── Header.vue
│   │   │   ├── Sidebar.vue
│   │   │   └── Main.vue
│   │   ├── Charts/
│   │   │   ├── UsageChart.vue
│   │   │   └── StatusChart.vue
│   │   └── Common/
│   │       ├── Pagination.vue
│   │       └── SearchBar.vue
│   ├── router/              # 路由配置
│   │   └── index.js
│   ├── stores/              # Pinia 状态管理
│   │   ├── user.js
│   │   ├── auth.js
│   │   └── app.js
│   ├── views/               # 页面组件
│   │   ├── Login.vue
│   │   ├── Dashboard.vue
│   │   ├── NetworkSegment/
│   │   ├── IPAddress/
│   │   ├── Device/
│   │   ├── Log/
│   │   └── ImportExport/
│   └── utils/               # 工具函数
│       ├── auth.js
│       ├── validators.js
│       └── formatters.js
├── public/                  # 静态资源
├── index.html
├── vite.config.js
├── package.json
└── Dockerfile
```

## 后端开发

### 添加新的 API 端点

1. **创建 Pydantic 模式** (`app/schemas/`)
   ```python
   # app/schemas/example.py
   from pydantic import BaseModel
   
   class ExampleCreate(BaseModel):
       name: str
       description: str
   
   class ExampleResponse(BaseModel):
       id: int
       name: str
       description: str
       
       class Config:
           from_attributes = True
   ```

2. **创建数据库模型** (`app/models/`)
   ```python
   # app/models/example.py
   from sqlalchemy import Column, Integer, String
   from app.core.database import Base
   
   class Example(Base):
       __tablename__ = "examples"
       
       id = Column(Integer, primary_key=True, index=True)
       name = Column(String(100), nullable=False)
       description = Column(String(500))
   ```

3. **创建 API 路由** (`app/api/`)
   ```python
   # app/api/examples.py
   from fastapi import APIRouter, Depends
   from sqlalchemy.orm import Session
   from app.core.database import get_db
   from app.schemas.example import ExampleCreate, ExampleResponse
   
   router = APIRouter()
   
   @router.post("/", response_model=ExampleResponse)
   def create_example(
       example: ExampleCreate,
       db: Session = Depends(get_db)
   ):
       # 实现逻辑
       pass
   ```

4. **注册路由** (`app/main.py`)
   ```python
   from app.api import examples
   
   app.include_router(
       examples.router,
       prefix="/api/v1/examples",
       tags=["Examples"]
   )
   ```

### 数据库迁移

```bash
# 初始化 Alembic（仅首次）
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "Add example table"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

### 添加业务逻辑服务

```python
# app/services/example_service.py
from sqlalchemy.orm import Session
from app.models.example import Example

class ExampleService:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, name: str, description: str):
        example = Example(name=name, description=description)
        self.db.add(example)
        self.db.commit()
        self.db.refresh(example)
        return example
    
    def get_by_id(self, example_id: int):
        return self.db.query(Example).filter(
            Example.id == example_id
        ).first()
```

## 前端开发

### 添加新页面

1. **创建页面组件** (`src/views/`)
   ```vue
   <!-- src/views/Example/List.vue -->
   <template>
     <div class="example-list">
       <el-table :data="tableData">
         <el-table-column prop="name" label="名称" />
         <el-table-column prop="description" label="描述" />
       </el-table>
     </div>
   </template>
   
   <script setup>
   import { ref, onMounted } from 'vue'
   import { getExamples } from '@/api/example'
   
   const tableData = ref([])
   
   const loadData = async () => {
     try {
       const data = await getExamples()
       tableData.value = data
     } catch (error) {
       console.error('Failed to load data:', error)
     }
   }
   
   onMounted(() => {
     loadData()
   })
   </script>
   ```

2. **添加 API 请求** (`src/api/`)
   ```javascript
   // src/api/example.js
   import request from './request'
   
   export function getExamples() {
     return request({
       url: '/api/v1/examples',
       method: 'get'
     })
   }
   
   export function createExample(data) {
     return request({
       url: '/api/v1/examples',
       method: 'post',
       data
     })
   }
   ```

3. **添加路由** (`src/router/index.js`)
   ```javascript
   {
     path: '/examples',
     name: 'Examples',
     component: () => import('@/views/Example/List.vue'),
     meta: { requiresAuth: true }
   }
   ```

### 状态管理

```javascript
// src/stores/example.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useExampleStore = defineStore('example', () => {
  const examples = ref([])
  
  const setExamples = (data) => {
    examples.value = data
  }
  
  const addExample = (example) => {
    examples.value.push(example)
  }
  
  return {
    examples,
    setExamples,
    addExample
  }
})
```

## 数据库管理

### 连接数据库

```bash
# 使用 Docker 容器
docker exec -it ipam-mysql mysql -u ipam -pipam_password ipam_db

# 使用本地 MySQL 客户端
mysql -h localhost -u ipam -pipam_password ipam_db
```

### 常用 SQL 命令

```sql
-- 查看所有表
SHOW TABLES;

-- 查看表结构
DESCRIBE users;

-- 查询数据
SELECT * FROM users LIMIT 10;

-- 备份数据库
-- 在命令行执行
mysqldump -u ipam -pipam_password ipam_db > backup.sql

-- 恢复数据库
mysql -u ipam -pipam_password ipam_db < backup.sql
```

## 测试

### 后端测试

```bash
# 安装测试依赖
pip install pytest pytest-cov httpx

# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app tests/

# 运行特定测试文件
pytest tests/test_api.py

# 运行特定测试函数
pytest tests/test_api.py::test_create_user
```

### 前端测试

```bash
# 安装测试依赖
npm install --save-dev vitest @vue/test-utils

# 运行测试
npm run test

# 运行测试并生成覆盖率报告
npm run test:coverage
```

## 代码规范

### Python 代码规范

- 遵循 PEP 8 规范
- 使用 Black 格式化代码
- 使用 Flake8 检查代码质量
- 使用 mypy 进行类型检查

```bash
# 安装工具
pip install black flake8 mypy

# 格式化代码
black app/

# 检查代码
flake8 app/

# 类型检查
mypy app/
```

### JavaScript 代码规范

- 使用 ESLint 检查代码
- 使用 Prettier 格式化代码

```bash
# 安装工具
npm install --save-dev eslint prettier

# 检查代码
npm run lint

# 格式化代码
npm run format
```

## 调试技巧

### 后端调试

1. **使用 print/logging**
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.info("Debug message")
   ```

2. **使用 pdb 调试器**
   ```python
   import pdb; pdb.set_trace()
   ```

3. **查看 SQL 查询**
   ```python
   # 在 database.py 中设置 echo=True
   engine = create_engine(settings.DATABASE_URL, echo=True)
   ```

### 前端调试

1. **使用 Vue DevTools**
   - 安装 Vue DevTools 浏览器扩展
   - 在开发模式下自动启用

2. **使用 console.log**
   ```javascript
   console.log('Debug:', data)
   console.table(tableData)
   ```

3. **使用浏览器调试器**
   - 在代码中添加 `debugger` 语句
   - 使用浏览器开发者工具设置断点

### Docker 调试

```bash
# 查看容器日志
docker-compose logs -f backend

# 进入容器
docker exec -it ipam-backend bash

# 查看容器资源使用
docker stats

# 重启容器
docker-compose restart backend
```

## 常用命令

### 后端

```bash
# 启动开发服务器
uvicorn app.main:app --reload

# 创建数据库迁移
alembic revision --autogenerate -m "message"

# 执行迁移
alembic upgrade head

# 运行测试
pytest

# 格式化代码
black app/
```

### 前端

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview

# 运行测试
npm run test

# 代码检查
npm run lint
```

### Docker

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 重新构建镜像
docker-compose build

# 清理未使用的资源
docker system prune -a
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 资源链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Vue 3 文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Docker 文档](https://docs.docker.com/)

祝开发愉快！🚀
