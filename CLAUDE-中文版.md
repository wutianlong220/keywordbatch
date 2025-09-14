# CLAUDE-中文版.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

这是一个基于 `keywords_tools` 参考文件夹中的 Chrome 扩展 MVP 的关键词处理工具项目。该项目将被初始化，创建一个具有翻译、Kdroi 计算和多平台链接生成功能的现代化关键词批量处理应用程序。

## 参考项目结构

`keywords_tools/` 文件夹包含一个可用的 Chrome 扩展 MVP，展示了：
- **文件处理**：支持拖放的 XLSX 文件批量处理
- **AI 集成**：DeepSeek API 集成用于关键词翻译
- **数据分析**：Kdroi 计算（搜索量 × CPC ÷ 关键词难度）
- **链接生成**：Google 搜索、Google Trends 和 Ahrefs 查询链接
- **UI 组件**：带有进度跟踪的弹出界面

## 关键参考文件

- `keywords_tools/popup.js:1` - 主要的关键词处理逻辑和 API 集成
- `keywords_tools/popup.html` - UI 结构和布局
- `keywords_tools/manifest.json` - Chrome 扩展配置
- `keywords_tools/background.js` - 后台服务工作线程
- `keywords_tools/README.md` - 完整的功能文档

## 技术栈（基于参考）

- **前端**：HTML5 + CSS3 + 原生 JavaScript (ES6+)
- **文件处理**：SheetJS (XLSX 库)
- **API 集成**：DeepSeek Chat Completions API
- **数据存储**：Chrome Storage API（用于扩展版本）

## 项目初始化命令

由于这是一个新项目，常用的开发命令将是：

```bash
# 初始化新项目（选择合适的模板）
npm init -y
# 或其他框架：
# python -m venv venv
# cargo init
# 等等

# 根据选择的技术栈安装依赖
npm install [依赖包]
# 或 pip install -r requirements.txt
# 等等

# 开发服务器
npm run dev
# 或 python main.py
# 等等

# 生产构建
npm run build
# 或等效命令
```

## 架构说明

参考实现遵循以下模式：
- **模块化设计**：为不同功能使用独立的类（KeywordProcessor）
- **事件驱动**：大量使用事件监听器进行用户交互
- **API 集成**：可配置的 API 端点和身份验证
- **文件处理**：大数据集的流式文件处理
- **进度跟踪**：实时进度更新和错误处理
- **数据验证**：输入验证和错误恢复

## 安全考虑

基于参考项目：
- **本地处理**：所有数据处理都在本地进行
- **API 安全**：API 密钥存储在本地，不在代码中
- **文件安全**：不上传文件到外部服务器
- **用户隐私**：所有数据保留在用户设备上

## 开发模式

在此代码库中工作时：
1. **参考 keywords_tools 文件夹** 获取实现细节
2. **遵循参考的模块化类结构**
3. **实现适当的错误处理** 和用户反馈
4. **使用 async/await 模式** 进行 API 调用和文件处理
5. **包含进度跟踪** 用于长时间运行的操作
6. **在整个处理流程中维护数据验证**