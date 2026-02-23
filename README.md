# Agentic Memory 

A novel agentic memory system for LLM agents that can dynamically organize memories in an agentic way.

## Introduction 

Large Language Model (LLM) agents have demonstrated remarkable capabilities in handling complex real-world tasks through external tool usage. However, to effectively leverage historical experiences, they require sophisticated memory systems. Traditional memory systems, while providing basic storage and retrieval functionality, often lack advanced memory organization capabilities.

Our project introduces an innovative **Agentic Memory** system that revolutionizes how LLM agents manage and utilize their memories:

<div align="center">
  <img src="Figure/intro-a.jpg" alt="Traditional Memory System" width="600"/>
  <img src="Figure/intro-b.jpg" alt="Our Proposed Agentic Memory" width="600"/>
  <br>
  <em>Comparison between traditional memory system (top) and our proposed agentic memory (bottom). Our system enables dynamic memory operations and flexible agent-memory interactions.</em>
</div>

> **Note:** This repository provides a memory system to facilitate agent construction. If you want to reproduce the results presented in our paper, please refer to: [https://github.com/WujiangXu/AgenticMemory](https://github.com/WujiangXu/AgenticMemory)

For more details, please refer to our paper: [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/pdf/2502.12110)


## Key Features 

-  Dynamic memory organization based on Zettelkasten principles
-  Intelligent indexing and linking of memories via ChromaDB
-  Comprehensive note generation with structured attributes
-  Interconnected knowledge networks
-  Continuous memory evolution and refinement
-  Agent-driven decision making for adaptive memory management

## Framework 

<div align="center">
  <img src="Figure/framework.jpg" alt="Agentic Memory Framework" width="800"/>
  <br>
  <em>The framework of our Agentic Memory system showing the dynamic interaction between LLM agents and memory components.</em>
</div>

## Project Structure 

```
A-Mem/
 agentic_memory/           # 核心库
    __init__.py           # 包初始化与公开接口声明
    memory_system.py      # 核心记忆系统（MemoryNote + AgenticMemorySystem）
    llm_controller.py     # LLM 后端控制器（OpenAI / Ollama）
    retrievers.py         # ChromaDB 向量检索器（普通 / 持久化 / 副本）
 examples/
    sovereign_memory.py   # 本地 Ollama 后端使用示例
 tests/                    # 单元测试
    conftest.py
    test_memory_system.py
    test_retriever.py
    test_utils.py
 Figure/                   # 论文配图
 .env                      # 环境变量配置文件（需自行填写密钥）
 pyproject.toml            # 项目元数据与依赖声明
 requirements.txt          # pip 依赖列表
 README.md
```

## Code Architecture 

### 1. `agentic_memory/memory_system.py`  核心记忆系统

#### `MemoryNote` 类

`MemoryNote` 是系统中最小的信息存储单元，代表**一条记忆笔记**。它封装了记忆的全部属性：

| 属性 | 类型 | 说明 |
|---|---|---|
| `content` | `str` | 记忆主体文本内容 |
| `id` | `str` | UUID 唯一标识符 |
| `keywords` | `List[str]` | LLM 提取的关键词列表 |
| `context` | `str` | LLM 生成的一句话语境摘要 |
| `tags` | `List[str]` | 分类标签，用于检索和归类 |
| `category` | `str` | 记忆类型（如 "Research"、"Task"） |
| `links` | `Dict` | 与其他记忆的关联 ID 集合 |
| `timestamp` | `str` | 创建时间戳（ISO 格式） |
| `last_accessed` | `str` | 最后访问时间戳 |
| `retrieval_count` | `int` | 被检索次数（使用频率统计） |
| `evolution_history` | `List` | 记忆演化历史记录 |

#### `AgenticMemorySystem` 类

系统核心类，负责记忆的完整生命周期管理。主要职责如下：

**初始化 (`__init__`)**
- 创建内存字典 `self.memories`（`id -> MemoryNote` 映射）
- 初始化 `ChromaRetriever` 向量数据库（每次启动会重置集合，保持无状态）
- 初始化 `LLMController` LLM 控制器
- 设置 `evo_threshold`（记忆演化阈值，默认 100 条触发一次 consolidation）

**核心方法**

| 方法 | 说明 |
|---|---|
| `analyze_content(content)` | 调用 LLM 从文本中提取 `keywords` / `context` / `tags` |
| `add_note(content, **kwargs)` | 新建 `MemoryNote`，触发 `process_memory` 演化流程，并写入 ChromaDB |
| `read(memory_id)` | 按 ID 读取记忆对象 |
| `update(memory_id, **kwargs)` | 更新记忆的任意字段，同步更新 ChromaDB |
| `delete(memory_id)` | 删除记忆（内存字典 + ChromaDB 同步删除） |
| `search(query, k)` | 基于 ChromaDB 语义相似度检索，返回 Top-K |
| `search_agentic(query, k)` | 增强检索：返回语义相似结果 + 链接邻居记忆 |
| `find_related_memories(query, k)` | 查找最近邻记忆（用于演化决策） |
| `find_related_memories_raw(query, k)` | 同上，但同时输出链接的邻居记忆（用于 prompt 构建） |
| `process_memory(note)` | 核心演化决策：调用 LLM 决定是否演化，执行 `strengthen` / `update_neighbor` |
| `consolidate_memories()` | 重建 ChromaDB 集合，对全量记忆进行索引整合 |

**记忆演化流程 (`process_memory`)**

```
新记忆  查找最近邻 (ChromaDB Top-5)
         
         
      构造 Prompt（含新记忆 + 邻居摘要）
         
         
      LLM 决策（JSON 输出）
         
      
                              
 strengthen（加强连接）  update_neighbor（更新邻居）
  - 更新新记忆的 links     - 更新邻居的 context
  - 更新新记忆的 tags      - 更新邻居的 tags
```

LLM 返回结构化 JSON，包含：
- `should_evolve`：是否需要演化
- `actions`：动作列表（`strengthen` / `update_neighbor`）
- `suggested_connections`：建议关联的邻居 ID
- `tags_to_update`：新记忆的新标签
- `new_context_neighborhood`：各邻居的新语境
- `new_tags_neighborhood`：各邻居的新标签列表

---

### 2. `agentic_memory/llm_controller.py`  LLM 后端控制器

采用**策略模式**，通过统一接口 `BaseLLMController.get_completion()` 屏蔽不同 LLM 后端的实现差异。

#### 类层次结构

```
BaseLLMController (ABC)
 OpenAIController     # 调用 OpenAI Chat Completions API（含 JSON Schema 强制输出）
 OllamaController     # 调用本地 Ollama（通过 LiteLLM 桥接，含空响应降级处理）

LLMController            # 工厂类，根据 backend 参数实例化具体控制器
```

#### `OpenAIController`
- 从环境变量 `OPENAI_API_KEY` 读取密钥（也可通过 `api_key` 参数传入）
- 强制使用 `response_format={"type": "json_schema", ...}` 确保结构化 JSON 输出
- 系统提示固定为 `"You must respond with a JSON object."`

#### `OllamaController`
- 通过 LiteLLM 调用 `ollama_chat/<model>` 端点
- 实现了 `_generate_empty_response` 降级方法：当 Ollama 无法生成结构化输出时，按 `response_format` 的 schema 生成空值响应，避免程序崩溃

#### `LLMController`（工厂类）

```python
LLMController(backend="openai", model="gpt-4o-mini", api_key=None)
# backend 支持 "openai" 或 "ollama"
```

---

### 3. `agentic_memory/retrievers.py`  向量检索器

基于 **ChromaDB** 实现的向量数据库封装，提供三种检索器：

#### `ChromaRetriever`（临时内存检索器）
- 使用 `chromadb.Client(Settings(allow_reset=True))` 创建**内存数据库**（进程退出后不保留）
- 使用 `SentenceTransformerEmbeddingFunction` 将文本转为稠密向量
- 存储时将 `list`/`dict` 序列化为 JSON 字符串（ChromaDB 元数据只支持标量）
- 检索时通过 `_convert_metadata_dict` 将字符串反序列化回原始类型

核心方法：

| 方法 | 说明 |
|---|---|
| `add_document(document, metadata, doc_id)` | 向集合添加文档（含自动序列化） |
| `delete_document(doc_id)` | 按 ID 删除文档 |
| `search(query, k)` | 向量相似度检索，返回 Top-K 含元数据结果 |
| `_convert_metadata_types(metadatas)` | 将检索结果的元数据从字符串还原为原始类型 |

#### `PersistentChromaRetriever`（持久化检索器）
- 继承自 `ChromaRetriever`，使用 `chromadb.PersistentClient` 将数据持久化到磁盘
- 支持 `extend=True` 参数，允许多 Agent 跨会话共享同一个记忆集合
- 默认存储路径：`~/.chromadb`

#### `CopiedChromaRetriever`（副本检索器）
- 继承自 `PersistentChromaRetriever`
- 将已有持久化集合复制到**临时目录**，为每个 Agent 创建隔离的副本
- 使用 `atexit.register(self.close)` 确保进程退出时自动清理临时文件
- 适用于多 Agent 需要从同一个起始记忆库出发、独立演化的场景

---

### 4. `examples/sovereign_memory.py`  本地部署示例

演示使用 **Ollama 本地后端**（`llama3` 模型）完整运行 A-MEM 系统的流程：初始化  添加记忆  语义检索。运行前需要安装并启动 Ollama 服务，并执行 `ollama pull llama3`。

---

## How It Works 

When a new memory is added to the system:
1. Generates comprehensive notes with structured attributes
2. Creates contextual descriptions and tags
3. Analyzes historical memories for relevant connections
4. Establishes meaningful links based on similarities
5. Enables dynamic memory evolution and updates

## Results 

Empirical experiments conducted on six foundation models demonstrate superior performance compared to existing SOTA baselines.

---

## Getting Started 

### Step 1: Clone the repository

```bash
git clone https://github.com/agiresearch/A-mem.git
cd A-mem
```

### Step 2: Configure environment variables

Copy the `.env` template and fill in your API key:

```bash
# 直接编辑 .env（项目根目录已提供模板）
```

编辑 `.env`，填入你的 OpenAI API Key（使用 OpenAI 后端时必填）：

```dotenv
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> 使用 Ollama 本地后端时，`.env` 无需填写 API Key，只需确保 Ollama 服务已启动。

---

### Step 3: Install dependencies

根据你的包管理工具，选择以下任意一种安装方式。

---

#### 方式一：使用 `pip` + `venv`（原生方式）

```bash
# 创建虚拟环境
python -m venv .venv

# 激活环境
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat

# 安装项目及依赖
pip install .

# 开发模式（可编辑安装，含测试工具）
pip install -e ".[dev]"
```

---

#### 方式二：使用 `conda`

推荐在 Python 数据科学生态（如 Anaconda / Miniconda）中使用此方式。

```bash
# 创建新的 conda 环境（Python 3.10 推荐，最低要求 3.8）
conda create -n amem python=3.10 -y

# 激活环境
conda activate amem

# 安装项目依赖
pip install .

# 开发模式（可编辑安装，含测试工具）
pip install -e ".[dev]"

# 安装 NLTK 所需的分词数据（首次运行需要）
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

> **说明**：ChromaDB 和 sentence-transformers 依赖 C++ 编译工具链，建议在安装前先执行
> `conda install -c conda-forge gcc`（Linux/macOS）以避免编译错误。

---

#### 方式三：使用 `uv`（现代高速包管理器）

[uv](https://github.com/astral-sh/uv) 是由 Astral 开发的极速 Python 包管理器，兼容 `pip` 接口并大幅提升安装速度。

```bash
# 安装 uv（若尚未安装）
# macOS / Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell):
irm https://astral.sh/uv/install.ps1 | iex

# 在项目根目录创建虚拟环境（自动选择 Python 版本）
uv venv --python 3.10

# 激活环境
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 安装项目（从 pyproject.toml 解析依赖）
uv pip install .

# 开发模式（可编辑安装，含测试工具）
uv pip install -e ".[dev]"

# 或者直接使用 uv sync（推荐，自动处理锁文件）
uv sync --extra dev
```

> **提示**：`uv` 的安装速度通常比 `pip` 快 10100 倍，适合 CI/CD 环境使用。

---

#### 方式四：仅安装依赖（不安装包本身）

```bash
# pip
pip install -r requirements.txt

# conda + pip
conda activate amem
pip install -r requirements.txt

# uv
uv pip install -r requirements.txt
```

---

### Step 4: Verify NLTK data

首次运行前需下载 NLTK 分词数据：

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

---

## Usage Examples 

### 基础使用（OpenAI 后端）

```python
import os
from dotenv import load_dotenv
from agentic_memory.memory_system import AgenticMemorySystem

# 加载 .env 配置
load_dotenv()

# 初始化记忆系统
memory_system = AgenticMemorySystem(
    model_name='all-MiniLM-L6-v2',  # 用于 ChromaDB 的嵌入模型
    llm_backend="openai",           # LLM 后端：openai 或 ollama
    llm_model="gpt-4o-mini"         # LLM 模型名称
)

# 添加记忆
memory_id = memory_system.add_note("Deep learning neural networks")

# 添加带元数据的记忆
memory_id = memory_system.add_note(
    content="Machine learning project notes",
    tags=["ml", "project"],
    category="Research",
    timestamp="202503021500"  # 格式：YYYYMMDDHHmm
)

# 按 ID 读取记忆
memory = memory_system.read(memory_id)
print(f"Content:  {memory.content}")
print(f"Tags:     {memory.tags}")
print(f"Context:  {memory.context}")
print(f"Keywords: {memory.keywords}")

# 语义检索（含链接邻居）
results = memory_system.search_agentic("neural networks", k=5)
for result in results:
    print(f"ID:      {result['id']}")
    print(f"Content: {result['content']}")
    print(f"Tags:    {result['tags']}")
    print("---")

# 更新记忆
memory_system.update(memory_id, content="Updated content about deep learning")

# 删除记忆
memory_system.delete(memory_id)
```

### 本地部署（Ollama 后端）

```bash
# 1. 安装并启动 Ollama：https://ollama.com/download

# 2. 拉取模型
ollama pull llama3

# 3. 运行示例
python examples/sovereign_memory.py
```

```python
from agentic_memory.memory_system import AgenticMemorySystem

memory_system = AgenticMemorySystem(
    model_name='all-MiniLM-L6-v2',
    llm_backend="ollama",
    llm_model="llama3"   # 或 "mistral"、"qwen2.5" 等本地模型
)
```

### 持久化记忆（跨会话）

```python
from agentic_memory.retrievers import PersistentChromaRetriever

retriever = PersistentChromaRetriever(
    directory="./my_memory_db",
    collection_name="agent_memories",
    model_name="all-MiniLM-L6-v2",
    extend=True  # 允许在已有集合基础上追加
)
```

### 多 Agent 隔离记忆

```python
from agentic_memory.retrievers import CopiedChromaRetriever

# 从共享基础记忆复制一个隔离副本，供单个 Agent 独立使用
retriever = CopiedChromaRetriever(
    directory="./shared_base_memory",
    collection_name="base_memories",
    model_name="all-MiniLM-L6-v2"
)
# 进程退出时自动清理临时目录
```

---

## Advanced Features 

### 1. ChromaDB Vector Storage 

- 高效向量嵌入存储与检索
- 快速语义相似度搜索
- 自动元数据序列化/反序列化处理
- 支持持久化存储与内存模式

### 2. Memory Evolution 

- 自动分析内容间的语义关联关系
- 根据相关记忆更新标签（`tags`）与语境（`context`）
- 在记忆之间建立语义连接（`links`）
- 两种演化动作：
  - **`strengthen`**：加强新记忆与邻居的连接，更新新记忆的标签
  - **`update_neighbor`**：根据新记忆的加入，更新邻居记忆的语境和标签

### 3. Flexible Metadata 

- 自定义标签（`tags`）与分类（`category`）
- LLM 自动关键词提取
- LLM 语境摘要生成
- 时间戳追踪（创建时间 + 最后访问时间）

### 4. Multiple LLM Backends 

| 后端 | 模型示例 | 适用场景 |
|---|---|---|
| `openai` | `gpt-4o`, `gpt-4o-mini` | 云端，高质量 |
| `ollama` | `llama3`, `qwen2.5`, `mistral` | 本地，数据主权 |

---

## Best Practices 

### Memory Creation 

- 提供清晰、具体的记忆内容
- 传入有意义的 `tags` 和 `category` 辅助组织
- LLM 会自动生成 `context` 和 `keywords`，无需手动填写

### Memory Retrieval 

- 使用与预期内容语义相近的查询词
- 根据需要调整 `k` 参数（默认返回 5 条）
- `search_agentic` 额外返回链接邻居，适合需要上下文关联的场景

### Memory Evolution 

- 允许系统自动演化，不必干预每次添加
- 当记忆量达到 `evo_threshold`（默认 100）时，系统会触发 `consolidate_memories` 重建索引
- 使用一致的标签命名规范，以提升演化质量

### Error Handling 

```python
try:
    results = memory_system.search_agentic("query", k=5)
    if results:
        for r in results:
            print(r["content"])
    else:
        print("No memories found.")
except Exception as e:
    print(f"Search failed: {e}")
```

---

## Running Tests 

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件并显示详情
pytest tests/test_memory_system.py -v

# 运行带覆盖率报告（需安装 pytest-cov）
pytest tests/ --cov=agentic_memory
```

---

## Citation 

If you use this code in your research, please cite our work:

```bibtex
@article{xu2025mem,
  title={A-mem: Agentic memory for llm agents},
  author={Xu, Wujiang and Liang, Zujie and Mei, Kai and Gao, Hang and Tan, Juntao and Zhang, Yongfeng},
  journal={arXiv preprint arXiv:2502.12110},
  year={2025}
}
```

## License 

This project is licensed under the MIT License. See LICENSE for details.
