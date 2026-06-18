# AI 产品经理学习平台

> **一个完整的 AI 产品经理学习项目** - 从语义检索、参数调优到评测体系，掌握 AI PM 的核心技能

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 项目简介

这是一个专为 **AI 产品经理求职** 设计的学习项目。通过一个完整的 AI 智能问答系统，你将掌握：

- ✅ **技术底层**：Embedding、向量检索、RAG、幻觉检测
- ✅ **参数调优**：Temperature、Top-p、Max tokens 的实际应用
- ✅ **产品能力**：Prompt 版本管理、评测体系、数据指标
- ✅ **简历亮点**：可演示的项目 + 可讲清的技术原理

**适合人群**：
- 准备投 AI 产品经理岗位的求职者
- 想要理解 AI 产品技术原理的产品经理
- 需要补齐 AI 知识的传统 PM

**学习时长**：3 周（核心功能已完成）

---

## ✨ 核心功能

### 1. 🤖 智能问答（语义检索）
- **真·语义检索**：使用 Embedding + FAISS 向量数据库，理解同义词和相关概念
- **幻觉检测**：自动检测 AI 回答中可能编造的内容
- **引用溯源**：展示答案的来源文档，提升可信度
- **性能监控**：实时显示响应时间、Token 消耗、成本

**学习目标**：理解 RAG 的完整流程、Embedding 的工作原理

### 2. 🎛️ 参数调优实验室
- **实时调节参数**：Temperature、Top-p、Max tokens
- **A/B 对比实验**：同一问题用不同参数对比效果
- **效果可视化**：直观理解参数对输出的影响

**学习目标**：掌握每个参数的作用、什么场景该用什么参数

### 3. 📝 Prompt 版本管理
- **版本化存储**：保存多个 Prompt 版本，记录改动原因
- **A/B 测试**：对比两个版本在同一问题上的表现
- **内置 3 个版本**：基础版、严格版（低幻觉）、友好版（用户体验）

**学习目标**：掌握 Prompt 工程、版本管理、效果对比

### 4. 📊 评测中心
- **批量评测**：上传测试集，自动跑完所有测试
- **LLM-as-judge**：用大模型给答案打分（可选）
- **指标统计**：准确率、成本、Token 消耗等
- **报告导出**：下载 CSV 格式的评测报告

**学习目标**：掌握 AI 产品的评测方法、LLM-as-judge 的原理

### 5. 📈 运营看板
- **核心指标**：交互量、采纳率、成本、响应时间
- **风险分析**：幻觉风险等级分布、趋势图
- **数据埋点**：记录每次交互的完整数据
- **日志导出**：支持导出交互日志

**学习目标**：掌握 AI 产品的指标体系、数据驱动决策

### 6. 💰 成本与延迟仪表盘
- **成本估算器**：输入业务量，估算月度/年度成本
- **模型成本对比**：一键对比所有模型，辅助选型决策
- **延迟分析**：P50/P90/P99 延迟分布，定位长尾问题

**学习目标**：掌握 AI PM 最值钱的硬技能——算账

### 7. 🛠️ Function Calling 演示
- **工具调用**：让 AI 主动调用计算器、天气、知识库等工具
- **执行轨迹**：可视化展示 AI 的"思考过程"（ReAct 循环）
- **Agent 雏形**：理解 AI 从"会聊天"到"会干活"的关键

**学习目标**：理解 Function Calling 和 Agent 的工作原理

### 🔧 FastAPI 评测微服务（后端）
- **独立后端服务**：LLM-as-judge 评测拆成独立的 FastAPI 微服务
- **前后端分离**：体现真实生产的架构（方案 C 的核心）
- **优雅降级**：微服务未启动时自动降级到本地调用
- **交互式文档**：访问 `http://localhost:8001/docs` 查看 API

**学习目标**：理解前后端分离架构、微服务设计

---

## 🚀 快速开始

### 1️⃣ 环境要求
- Python 3.10+
- 8GB+ RAM（首次加载 Embedding 模型需要）
- 稳定的网络（调用 LLM API）

### 2️⃣ 安装依赖

```bash
# 克隆项目
cd AI-PM-Master

# 安装依赖
pip install -r requirements.txt

# 国内用户加速（推荐）
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
```

**依赖说明**：
- `sentence-transformers`：本地 Embedding 模型（首次会自动下载约 118MB）
- `faiss-cpu`：向量检索引擎
- `streamlit`：前端界面
- `openai`：兼容多家大模型 API

### 3️⃣ 配置 API Key

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API 密钥
```

`.env` 文件示例：

```env
# MiniMax（推荐，新用户有免费额度）
LLM_BASE_URL=https://api.minimax.chat/v1
LLM_API_KEY=你的-api-key
LLM_MODEL=abab6.5-chat

# 或者使用其他兼容 OpenAI 格式的 API
# 通义千问、DeepSeek、OpenAI 都支持
```

**API 申请地址**：
- [MiniMax](https://api.minimax.chat/) - 新用户有免费额度
- [DeepSeek](https://platform.deepseek.com/) - 价格最低
- [通义千问](https://dashscope.aliyun.com/) - 阿里云

### 4️⃣ 启动应用

```bash
streamlit run main.py
```

成功启动后，浏览器会自动打开 `http://localhost:8501`

**首次启动**：
- 会自动下载 Embedding 模型（约 118MB）
- 会自动构建向量索引（几秒钟）
- 之后启动会很快（直接加载已构建的索引）

---

## 📁 项目结构

```
AI-PM-Master/
│
├── main.py                          # 主应用：智能问答
├── config.py                        # 全局配置
├── requirements.txt                 # Python 依赖
├── .env.example                     # 环境变量模板
│
├── src/                             # 核心模块
│   ├── vector_rag.py                # 语义检索引擎（Embedding + FAISS）
│   ├── llm_client.py                # LLM 调用客户端（含 Function Calling）
│   ├── prompt_manager.py            # Prompt 版本管理
│   ├── hallucination_detector.py   # 幻觉检测
│   ├── analytics.py                 # 数据埋点与统计
│   ├── evaluator.py                 # 评测模块
│   ├── cost_analyzer.py             # 成本估算与延迟分析
│   ├── tools.py                     # Function Calling 工具集
│   └── judge_client.py              # 评测微服务客户端（优先远程/降级本地）
│
├── evaluation_service/              # FastAPI 评测微服务（后端）
│   ├── main.py                      # 服务入口（/judge 接口）
│   ├── models.py                    # Pydantic 数据模型
│   └── evaluator.py                 # LLM-as-judge 评测逻辑
│
├── pages/                           # Streamlit 多页面（前端）
│   ├── 1_参数调优实验室.py
│   ├── 2_Prompt版本管理.py
│   ├── 3_评测中心.py
│   ├── 4_运营看板.py
│   ├── 5_成本与延迟仪表盘.py
│   └── 6_FunctionCalling演示.py
│
├── data/                            # 数据目录
│   ├── knowledge_base/              # 知识库文档（.txt）
│   ├── prompts/                     # Prompt 版本（.json）
│   ├── test_sets/                   # 测试集（.csv）
│   └── logs/                        # 交互日志（.jsonl）
│
├── PRD/                             # 产品文档
│   ├── 产品需求文档.md
│   └── 技术选型决策文档.md          # Prompt vs RAG vs 微调
│
├── Dockerfile                       # Docker 镜像
├── docker-compose.yml               # 一键启动前端+后端
├── start_all.bat / start_all.sh     # 本地同时启动前后端
│
├── AI产品经理知识点全解.md          # 知识点文档
├── 代码完全解析.md                   # 代码详细解析
└── README.md                        # 本文件
```

---

## 📚 配套文档

| 文档 | 内容 | 适合谁 |
|------|------|--------|
| [AI产品经理知识点全解.md](AI产品经理知识点全解.md) | 从 Token、Temperature 到 RAG、幻觉检测的全部知识点 | 所有人，面试必看 |
| [代码完全解析.md](代码完全解析.md) | 每个文件、每行代码的详细解释 | 想深入理解代码的人 |
| [产品需求文档.md](PRD/产品需求文档.md) | 完整的 PRD，包含需求、指标、技术方案 | 学习产品能力 |
| [技术选型决策文档.md](PRD/技术选型决策文档.md) | Prompt vs RAG vs 微调，模型/向量库/框架选型 | 战略思维，面试高频 |

---

## 🔧 启动方式（两种）

### 方式一：只启动前端（最简单，适合学习）
```bash
streamlit run main.py
```
评测中心的 LLM-as-judge 会自动降级到本地调用，功能不受影响。

### 方式二：前端 + 后端微服务（完整方案 C 架构）
```bash
# Windows
start_all.bat

# Mac/Linux
./start_all.sh
```
这会同时启动：
- Streamlit 前端：`http://localhost:8501`
- FastAPI 后端：`http://localhost:8001/docs`（可查看交互式 API 文档）

### 方式三：Docker 一键部署（生产形态）
```bash
docker compose up
```

---

## 🎯 学习路径

### 第 1 周：理解核心概念
1. 阅读 [AI产品经理知识点全解.md](AI产品经理知识点全解.md)
2. 在主页提几个问题，观察系统如何工作
3. 进入"参数调优实验室"，调节 Temperature，观察变化
4. 理解 Token、上下文窗口、RAG 的基本概念

### 第 2 周：深入技术细节
1. 阅读 [代码完全解析.md](代码完全解析.md)，理解代码实现
2. 在"Prompt 版本管理"中对比不同版本的效果
3. 在"评测中心"跑一次完整评测
4. 理解 Embedding、向量检索、幻觉检测的原理

### 第 3 周：产品思维 + 简历准备
1. 阅读 [产品需求文档.md](PRD/产品需求文档.md)，学习 PRD 的写法
2. 在"运营看板"查看数据指标，理解数据驱动决策
3. 总结学到的知识点，写进简历
4. 准备面试话术

---

## 💡 如何写进简历

### 项目描述示例

```
AI 智能问答系统 | 独立开发 | 2024.06

- 设计并开发基于 RAG 的智能问答系统，实现语义检索、参数调优、评测体系等完整功能
- 技术栈：Python + Streamlit + sentence-transformers + FAISS + OpenAI API
- 核心亮点：
  1. 实现真·语义检索（Embedding + 向量数据库），检索准确率提升 40%
  2. 设计幻觉检测算法，自动识别 AI 编造的内容，降低风险
  3. 建立 Prompt 版本管理和 A/B 测试流程，支持快速迭代
  4. 搭建完整的评测体系（LLM-as-judge + 标准测试集），准确率达 75%
  5. 设计 AI 产品指标体系（采纳率、拒答率、幻觉率、成本等）

- 产品能力：独立完成 PRD、指标设计、数据埋点、A/B 测试全流程
- 技术深度：熟悉 LLM 调用参数、RAG 工作原理、向量检索、幻觉检测
```

### 面试话术

**面试官**："你说你懂 RAG，那 Embedding 是怎么工作的？"

**你**："Embedding 是把文本转换为数字向量的技术。在我的项目中，我用 sentence-transformers 模型把知识库文档和用户问题都转换为 384 维的向量。语义相近的文本，向量也相近，这样就能通过余弦相似度找到最相关的文档。相比关键词匹配，Embedding 能理解同义词，比如'手机配对'和'蓝牙连接'能匹配上。我用 FAISS 做向量索引，检索速度在毫秒级。"

**面试官**："怎么降低幻觉？"

**你**："我在项目里用了几个方法：1）RAG 提供文档依据，让 AI 照着文档答；2）Temperature 设为 0.3，降低随机性；3）System Prompt 明确约束'不能编造'；4）我还实现了幻觉检测算法，提取 AI 回答的关键词，检查有多少能在原文档中找到支撑，支撑率低于 50% 就标记为高风险。这个方法不需要标准答案，能自动检测。"

---

## 🔧 常见问题

### Q1：Embedding 模型下载很慢怎么办？
A：首次运行会自动下载约 118MB 的模型，国内可能较慢。可以：
1. 使用镜像源：设置环境变量 `HF_ENDPOINT=https://hf-mirror.com`
2. 或手动下载后放到 `~/.cache/huggingface/` 目录

### Q2：如何添加自己的知识库？
A：在 `data/knowledge_base/` 目录下添加 `.txt` 文件，每个文件是一个主题的知识文档。重启应用，系统会自动构建向量索引。

### Q3：支持哪些大模型？
A：支持所有兼容 OpenAI API 格式的模型，包括：
- MiniMax（推荐，免费额度）
- 通义千问
- DeepSeek（价格最低）
- OpenAI GPT
- 智谱 GLM
- 本地模型（Ollama）

只需修改 `.env` 文件中的 `LLM_BASE_URL` 和 `LLM_MODEL`。

### Q4：成本大概多少？
A：取决于使用量和模型：
- 学习阶段（50-100 次交互）：约 ¥5-20
- 评测 100 题：约 ¥10-30
- 使用 DeepSeek 可以降低 50% 成本

### Q5：能部署到云端吗？
A：可以。推荐方案：
- Streamlit Community Cloud（免费，但有资源限制）
- Railway / Render（免费层可用）
- 阿里云 / 腾讯云（需付费）

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

**贡献方向**：
- 添加更多 Prompt 版本示例
- 优化幻觉检测算法
- 添加更多评测指标
- 优化文档和注释

---

## 📄 许可证

MIT License - 自由使用、修改、分发

---

## 🙏 致谢

- **Streamlit** - 优雅的 Web 界面框架
- **Sentence Transformers** - 强大的 Embedding 模型
- **FAISS** - 高效的向量检索引擎
- **OpenAI** - 统一的 LLM API 标准

---

## 📞 联系方式

- GitHub Issues: 项目问题请提 Issue
- 技术交流：欢迎 Star 和 Fork

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star ⭐**

Made with ❤️ for AI Product Managers

</div>
