---
inclusion: always
---

# CineTune Monorepo 项目结构指南

> 📅 创建日期: 2026-01-22  
> 🎯 目标: 说明 Monorepo 的组织结构和工作流程  
> 📌 类型: Always-included Steering

---

## 📁 项目结构

```
CineTune-Monorepo/              # 父仓库（主仓库）
├── .git/                       # 父仓库的 Git 配置
├── .gitignore                  # 父仓库的忽略规则
├── .gitmodules                 # 子模块配置文件
├── .kiro/                      # Kiro AI 配置（父仓库级别）
│   ├── steering/               # 全局 steering 规则
│   │   ├── project-guidelines.md      # 项目开发指南
│   │   ├── design-system.md           # 设计系统规范
│   │   └── monorepo-structure.md      # 本文件
│   └── specs/                  # 全局 specs（跨项目功能）
├── README.md                   # 主仓库说明文档
├── docs/                       # 📚 共享文档目录（前后端共享）
│   ├── README.md               # 文档导航中心
│   ├── API接口文档.md          # 前后端接口规范（单一数据源）
│   ├── 产品需求总览.md         # 产品需求和功能规划
│   ├── 文档格式规范.md         # 文档编写标准
│   ├── 前端/                   # 前端相关文档
│   │   ├── 技术文档/
│   │   ├── 需求清单/
│   │   └── 问题排查/
│   ├── 后端/                   # 后端相关文档
│   │   ├── 已实现功能/
│   │   ├── 技术文档/
│   │   ├── 测试文档/
│   │   ├── 需求清单/
│   │   └── 问题排查/
│   ├── 部署运维/               # 部署和运维文档
│   └── 归档/                   # 过期文档归档
├── frontend/                   # 🎨 前端子模块（Git Submodule）
│   ├── .git                    # 指向 CineTuneFrontend 仓库
│   ├── src/                    # React Native 源代码
│   ├── package.json
│   └── ...                     # 其他前端文件
└── backend/                    # ⚙️ 后端子模块（Git Submodule）
    ├── .git                    # 指向 YingJiang-AI 仓库
    ├── backend/                # FastAPI 源代码
    ├── requirements.txt
    └── ...                     # 其他后端文件
```

---

## 🔑 核心概念

### 1. Git Submodules（子模块）

**什么是子模块？**
- `frontend/` 和 `backend/` 是独立的 Git 仓库
- 它们通过 Git Submodules 机制链接到父仓库
- 每个子模块都有自己的 Git 历史和远程仓库

**子模块的特点：**
- ✅ 独立开发：可以单独克隆、提交、推送
- ✅ 版本锁定：父仓库记录子模块的特定提交
- ✅ 独立部署：前后端可以独立部署和发布
- ⚠️ 需要额外操作：更新子模块需要特殊命令

### 2. 共享文档目录（docs/）

**为什么需要共享文档？**
- 前后端需要共享 API 接口定义
- 产品需求需要前后端都了解
- 避免文档分散和不一致

**文档管理原则：**
- ✅ 单一数据源：API 接口只在 `docs/API接口文档.md` 定义
- ✅ 前后端共享：所有团队成员都能访问
- ✅ 版本控制：文档变更通过 Git 追踪
- ✅ 集中管理：避免文档分散在各个子仓库

---

## 🔄 工作流程

### 克隆项目

**首次克隆（包含所有子模块）：**
```bash
git clone --recurse-submodules https://github.com/papysans/CineTune-Monorepo.git
```

**如果已经克隆了父仓库：**
```bash
cd CineTune-Monorepo
git submodule update --init --recursive
```

### 在子模块中工作

**进入子模块目录：**
```bash
# 前端开发
cd frontend

# 后端开发
cd backend
```

**在子模块中的 Git 操作：**
```bash
# 查看状态
git status

# 切换分支
git checkout dev

# 创建新分支
git checkout -b feature/new-feature

# 提交更改
git add .
git commit -m "feat: add new feature"

# 推送到远程
git push origin feature/new-feature
```

**重要提示：**
- 子模块中的 Git 操作与普通仓库完全相同
- 子模块的更改不会自动反映到父仓库
- 需要在父仓库中提交子模块的引用更新

### 更新子模块引用

**当子模块有新提交时：**
```bash
# 在父仓库根目录
cd CineTune-Monorepo

# 更新子模块到最新提交
git submodule update --remote frontend
# 或
git submodule update --remote backend

# 提交子模块引用的更新
git add frontend  # 或 backend
git commit -m "chore: update frontend submodule to latest"
git push
```

### 更新共享文档

**文档更新流程：**
```bash
# 在父仓库根目录
cd CineTune-Monorepo

# 编辑文档
# 例如：编辑 docs/API接口文档.md

# 提交文档更改
git add docs/
git commit -m "docs: update API documentation"
git push
```

**文档更新原则：**
- ✅ API 接口变更：必须先更新 `docs/API接口文档.md`
- ✅ 功能完成：更新对应的已实现功能文档
- ✅ 遇到问题：立即创建问题排查文档
- ✅ 新需求：更新需求清单

---

## 📋 常见场景

### 场景 1：开发新的前端功能

```bash
# 1. 进入前端子模块
cd frontend

# 2. 切换到开发分支
git checkout dev

# 3. 拉取最新代码
git pull origin dev

# 4. 创建功能分支
git checkout -b feature/new-ui

# 5. 开发功能...

# 6. 提交更改
git add .
git commit -m "feat: add new UI component"
git push origin feature/new-ui

# 7. 回到父仓库，更新文档
cd ..
# 编辑 docs/前端/已实现功能/...

# 8. 提交文档更新
git add docs/
git commit -m "docs: document new UI component"
git push
```

### 场景 2：开发新的后端 API

```bash
# 1. 先更新 API 文档
cd CineTune-Monorepo
# 编辑 docs/API接口文档.md

git add docs/API接口文档.md
git commit -m "docs: add new API endpoint definition"
git push

# 2. 进入后端子模块
cd backend

# 3. 切换到开发分支
git checkout dev

# 4. 实现 API...

# 5. 提交更改
git add .
git commit -m "feat: implement new API endpoint"
git push origin dev

# 6. 回到父仓库，更新已实现功能文档
cd ..
# 编辑 docs/后端/已实现功能/...

git add docs/
git commit -m "docs: document API implementation"
git push
```

### 场景 3：前后端联调

```bash
# 1. 确保前后端都在最新的 dev 分支
cd frontend
git checkout dev
git pull origin dev

cd ../backend
git checkout dev
git pull origin dev

# 2. 查看 API 文档
cd ..
# 查看 docs/API接口文档.md

# 3. 启动后端服务
cd backend
# 启动后端...

# 4. 启动前端应用
cd ../frontend
# 启动前端...

# 5. 联调测试...

# 6. 如果发现问题，记录到问题排查文档
cd ..
# 创建 docs/前端/问题排查/问题_描述_2026-01-22.md
# 或 docs/后端/问题排查/问题_描述_2026-01-22.md
```

### 场景 4：同步其他开发者的更改

```bash
# 1. 更新父仓库
cd CineTune-Monorepo
git pull

# 2. 更新所有子模块
git submodule update --remote

# 3. 查看文档更新
# 检查 docs/ 目录中的新文档或更新
```

---

## ⚠️ 重要注意事项

### 子模块的特殊性

1. **子模块不会自动更新**
   - 拉取父仓库不会自动更新子模块
   - 需要手动执行 `git submodule update`

2. **子模块的分支管理**
   - 子模块默认处于"分离头指针"状态
   - 开发前务必切换到具体分支（如 `dev`）

3. **子模块的提交顺序**
   - 先在子模块中提交和推送
   - 再在父仓库中更新子模块引用

### 文档管理

1. **docs/ 目录属于父仓库**
   - 不要在子模块中创建或修改 docs/
   - 所有文档更改在父仓库中进行

2. **文档与代码的同步**
   - API 文档先于代码更新
   - 功能完成后立即更新文档
   - 文档和代码分别提交（不同仓库）

3. **避免文档冲突**
   - 多人协作时注意文档更新
   - 使用清晰的文件命名（包含日期）
   - 优先更新现有文档，避免创建重复文档

---

## 🎯 最佳实践

### 开发流程

1. ✅ **查看文档** → 了解需求和接口定义
2. ✅ **更新文档** → 如果需要新增或修改接口
3. ✅ **开发功能** → 在对应的子模块中开发
4. ✅ **测试验证** → 确保功能正常工作
5. ✅ **提交代码** → 在子模块中提交和推送
6. ✅ **更新文档** → 记录已实现功能和遇到的问题
7. ✅ **更新引用** → 在父仓库中更新子模块引用（可选）

### 团队协作

1. ✅ **定期同步**
   - 每天开始工作前拉取最新代码
   - 包括父仓库和子模块

2. ✅ **清晰沟通**
   - API 变更通知前后端
   - 文档更新及时同步

3. ✅ **避免冲突**
   - 前后端分工明确
   - 文档更新使用不同文件（带日期）

---

## 🔧 常用命令速查

### 父仓库操作

```bash
# 克隆项目（包含子模块）
git clone --recurse-submodules <repo-url>

# 初始化子模块（如果已克隆父仓库）
git submodule update --init --recursive

# 更新所有子模块到最新
git submodule update --remote

# 更新特定子模块
git submodule update --remote frontend
git submodule update --remote backend

# 查看子模块状态
git submodule status

# 提交子模块引用更新
git add frontend backend
git commit -m "chore: update submodules"
git push
```

### 子模块操作

```bash
# 进入子模块
cd frontend  # 或 cd backend

# 查看当前分支
git branch

# 切换分支
git checkout dev

# 拉取最新代码
git pull origin dev

# 创建新分支
git checkout -b feature/new-feature

# 提交更改
git add .
git commit -m "feat: add feature"
git push origin feature/new-feature

# 返回父仓库
cd ..
```

### 文档操作

```bash
# 在父仓库根目录

# 查看文档结构
ls docs/

# 编辑文档（使用你喜欢的编辑器）
# 例如：code docs/API接口文档.md

# 提交文档更改
git add docs/
git commit -m "docs: update documentation"
git push
```

---

## 💡 提示

- 📖 不确定时，先查看 `docs/` 中的文档
- 🔄 定期同步父仓库和子模块
- 📝 文档和代码分开提交（不同仓库）
- ⚠️ 子模块操作前确保在正确的分支
- 🎯 API 变更必须先更新文档
- 🔍 遇到问题先查看问题排查文档
- 📚 优先更新现有文档，避免创建重复文档

---

## 🔗 相关文档

- [项目开发指南](./project-guidelines.md) - 详细的开发规范
- [设计系统规范](./design-system.md) - UI/UX 设计规范
- [文档格式规范](../../docs/文档格式规范.md) - 文档编写标准
- [API接口文档](../../docs/API接口文档.md) - 前后端接口定义

---

**最后更新**: 2026-01-22  
**维护者**: CineTune开发团队
