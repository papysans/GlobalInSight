---
inclusion: always
---

# CineTune 设计系统规则

基于代码库分析生成的设计系统规则，用于 Figma MCP 集成。

## 项目概述

**CineTune** 是一个电影感图片自动处理系统，包含：
- **后端**: Python FastAPI + MetaGPT 多 Agent 协作
- **前端**: 微信小程序 (Taro + TypeScript + Vant UI)
- **核心功能**: AI 智能构图分析 + 电影级调色处理

## 技术栈架构

### 后端技术栈
```
核心框架:    FastAPI (Python 3.10+)
数据库:      PostgreSQL 14+
ORM:         SQLAlchemy 2.0 + Alembic
认证:        PyJWT + Passlib
任务队列:    Celery + Redis
缓存:        Redis
AI框架:      MetaGPT + OpenAI API
图像处理:    OpenCV + Pillow
日志:        Loguru
部署:        Docker + Nginx + Uvicorn
```

### 前端技术栈
```
跨端框架:    Taro 4.x
UI组件库:    Vant Weapp (通过 @antmjs/vantui)
状态管理:    Redux + Redux Toolkit
类型系统:    TypeScript 5.0+
工具库:      ahooks (优先使用)
HTTP客户端:  ahooks useRequest
日期处理:    Day.js
工具函数:    Lodash-es
图表库:      ECharts (echarts-for-weixin)
```

## 设计系统结构

### 1. Token 定义

#### 颜色系统 (基于 Vant UI 主题)
```scss
// 主题色
$primary-color: #1989fa;    // 主品牌色
$success-color: #07c160;    // 成功色
$warning-color: #ff976a;    // 警告色
$danger-color: #ee0a24;     // 危险色
$info-color: #909399;       // 信息色

// 文字色
$text-primary: #323233;     // 主要文字
$text-regular: #646566;     // 常规文字
$text-secondary: #969799;   // 次要文字
$text-placeholder: #c8c9cc; // 占位符文字

// 边框色
$border-color: #ebedf0;     // 边框色

// 背景色
$bg-color: #f7f8fa;        // 页面背景
$bg-white: #ffffff;        // 白色背景
```

#### 间距系统
```scss
$spacing-xs: 8px;   // 4rpx
$spacing-sm: 12px;  // 24rpx
$spacing-md: 16px;  // 32rpx
$spacing-lg: 24px;  // 48rpx
$spacing-xl: 32px;  // 64rpx
```

#### 字体系统 (小程序 rpx 单位)
```scss
$font-size-xs: 20rpx;  // 10px
$font-size-sm: 24rpx;  // 12px
$font-size-md: 28rpx;  // 14px
$font-size-lg: 32rpx;  // 16px
$font-size-xl: 36rpx;  // 18px
```

#### 圆角系统
```scss
$border-radius-sm: 4px;   // 8rpx
$border-radius-md: 8px;   // 16rpx
$border-radius-lg: 16px;  // 32rpx
```

### 2. 组件库架构

#### 组件优先级
```
1. Vant UI 组件（优先使用）
2. ahooks Hooks（优先使用）
3. 成熟开源方案（如 ECharts）
4. 自行实现（最后选择）
```

#### 核心组件映射
```typescript
// 基础组件
Button, Cell, Icon, Image, Popup - @antmjs/vantui
Loading, Toast, Dialog, Notify - @antmjs/vantui

// 表单组件
Field, Form, Checkbox, Radio, Switch - @antmjs/vantui

// 展示组件
Tag, Badge, Empty, Skeleton, Divider - @antmjs/vantui

// 导航组件
Tab, Tabs, Sidebar, TreeSelect - @antmjs/vantui

// 自定义组件（Vant 未提供）
ImageUploader, ImageCropper, StyleSelector, ResultViewer
```

### 3. 页面结构规范

#### 小程序页面路由
```typescript
pages: [
  'pages/index/index',           // 首页（生成页）
  'pages/auth/login/index',      // 登录
  'pages/auth/register/index',   // 注册
  'pages/generation/result/index', // 结果页
  'pages/user/profile/index',    // 用户中心
  'pages/user/history/index',    // 历史记录
  'pages/user/recharge/index',   // 充值页
]

tabBar: [
  { pagePath: 'pages/index/index', text: '生成' },
  { pagePath: 'pages/user/history/index', text: '历史' },
  { pagePath: 'pages/user/profile/index', text: '我的' }
]
```

#### 目录结构模式
```
src/
├── components/           # 公共组件
│   ├── common/          # 通用组件 (Loading, Empty, ImageUploader)
│   ├── user/            # 用户相关组件 (CreditBadge, MemberBadge)
│   └── generation/      # 生成相关组件 (StyleSelector, ResultViewer)
├── pages/               # 页面组件
├── services/            # API服务
├── types/               # TypeScript类型定义
├── utils/               # 工具函数
├── model/               # Redux状态管理
└── scss/                # 全局样式
```

### 4. 样式架构

#### CSS Modules 模式
```tsx
// 组件文件结构
Component/
├── index.tsx
├── index.module.scss
└── types.ts

// 使用方式
import styles from './index.module.scss'
<View className={styles.container}>
```

#### 响应式单位 (小程序专用)
```scss
// rpx 转换规则
// 设计稿宽度: 750px
// 1rpx = 屏幕宽度 / 750
.container {
  width: 750rpx;        // 屏幕宽度
  padding: 32rpx;       // 16px
  font-size: 28rpx;     // 14px
}
```

### 5. 图标系统

#### 图标来源
```
1. Vant UI 内置图标 (优先)
2. 自定义图标资源 (assets/icons/)
3. 图标字体 (iconfont)
```

#### 图标使用规范
```tsx
// Vant 内置图标
<Icon name="success" size="20px" color="#07c160" />

// 自定义图标
<Image src="/assets/icons/custom-icon.png" className="icon" />
```

### 6. 资产管理

#### 图片资源
```
assets/
├── images/              # 图片资源
│   ├── logo.png        # 应用Logo
│   ├── placeholder.png # 占位图
│   └── backgrounds/    # 背景图
└── icons/              # 图标资源
    ├── home.png
    ├── home-active.png
    └── ...
```

#### 图片优化策略
```tsx
// 小程序原生懒加载
<Image src={url} lazyLoad mode="aspectFill" />

// 图片压缩
Taro.compressImage({
  src: tempFilePath,
  quality: 80
})
```

### 7. 状态管理架构

#### Redux Toolkit 模式
```typescript
// Store 结构
store/
├── index.ts            # Store 配置
├── user.ts             # 用户状态
├── credit.ts           # 积分状态
└── app.ts              # 应用全局状态

// Slice 模式
const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: { ... },
  extraReducers: { ... }
})
```

### 8. API 接口规范

#### 统一响应格式
```typescript
interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 成功响应
{ code: 200, message: "success", data: {...} }

// 错误响应
{ code: 400, message: "参数错误", error: "详细错误信息" }
```

#### 接口调用规范
```typescript
// 统一使用 ahooks useRequest
const { data, loading, error, run } = useRequest(apiFunction, {
  onSuccess: (data) => { ... },
  onError: (error) => { ... }
})
```

### 9. 微信小程序特有功能

#### 微信登录流程
```
1. wx.login() 获取 code
2. 发送 code 到后端换取 openid
3. 后端查询/创建用户
4. 返回 JWT token
5. 前端存储 token
```

#### 微信授权组件
```tsx
// 头像选择 (新版API)
<Button openType="chooseAvatar" onChooseAvatar={onChooseAvatar}>
  选择头像
</Button>

// 昵称输入
<Input type="nickname" onInput={onNicknameInput} />

// 手机号获取
<Button openType="getPhoneNumber" onGetPhoneNumber={onGetPhoneNumber}>
  获取手机号
</Button>
```

## Figma 集成指导原则

### 1. 设计转代码规则

- **优先使用 Vant UI 组件**: 将 Figma 设计映射到对应的 Vant 组件
- **保持设计系统一致性**: 使用定义的颜色、字体、间距 token
- **响应式适配**: 将 px 单位转换为 rpx (小程序专用)
- **组件复用**: 重用现有组件而非重复实现

### 2. 组件映射策略

```
Figma Button → Vant Button
Figma Input → Vant Field
Figma Card → Vant Cell/Card
Figma Modal → Vant Popup/Dialog
Figma Loading → Vant Loading
Figma Toast → Vant Toast
```

### 3. 样式转换规则

```scss
// Figma 设计 → 小程序样式
width: 375px → width: 750rpx
padding: 16px → padding: 32rpx
font-size: 14px → font-size: 28rpx
border-radius: 8px → border-radius: 16rpx
```

### 4. 代码生成模板

```tsx
// 标准组件模板
import { View, Text } from '@tarojs/components'
import { Button, Field } from '@antmjs/vantui'
import { useRequest } from 'ahooks'
import { FC } from 'react'
import styles from './index.module.scss'

interface ComponentProps {
  // 类型定义
}

const Component: FC<ComponentProps> = (props) => {
  // ahooks 逻辑
  const { data, loading } = useRequest(apiFunction)

  return (
    <View className={styles.container}>
      {/* Vant UI 组件 */}
    </View>
  )
}

export default Component
```

### 5. 性能优化指导

- **图片懒加载**: 使用小程序原生 lazyLoad
- **虚拟列表**: 长列表使用 VirtualList
- **分包加载**: 按功能模块分包
- **缓存策略**: 合理使用 ahooks 缓存功能

## 业务特定组件

### 1. 图片处理相关
```tsx
// 图片上传组件
<ImageUploader onUpload={handleUpload} maxSize={10 * 1024 * 1024} />

// 图片裁剪组件
<ImageCropper src={imageSrc} onCrop={handleCrop} />

// 风格选择器
<StyleSelector presets={presets} onSelect={handleSelect} />

// 结果查看器
<ResultViewer images={resultImages} onDownload={handleDownload} />
```

### 2. 用户系统相关
```tsx
// 积分徽章
<CreditBadge credits={userCredits} />

// 会员徽章
<MemberBadge level={memberLevel} />

// 充值套餐卡片
<RechargePackageCard package={packageInfo} onSelect={handleSelect} />
```

### 3. 生成任务相关
```tsx
// 任务状态指示器
<TaskStatusIndicator status={taskStatus} />

// 处理进度条
<ProcessingProgress progress={progress} estimatedTime={estimatedTime} />

// 历史记录卡片
<HistoryCard task={taskInfo} onView={handleView} />
```

---

**注意**: 本设计系统规则基于当前代码库分析生成，在使用 Figma MCP 时应：
1. 优先使用已定义的组件和样式 token
2. 保持与现有技术栈的一致性
3. 遵循小程序开发规范和限制
4. 确保生成的代码可以直接在项目中使用