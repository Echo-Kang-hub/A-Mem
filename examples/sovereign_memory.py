import os
import sys

# 确保可以从源代码目录导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic_memory.memory_system import AgenticMemorySystem

def main():
    """
    示例主函数，展示如何初始化记忆系统并进行存储和检索操作。
    """
    print("🧠 初始化 A-mem 主权系统（本地）...")
    
    # 使用本地后端初始化记忆系统
    # 注意：需要 Ollama 运行并拉取 "llama3" 模型
    try:
        memory_system = AgenticMemorySystem(
            model_name='all-MiniLM-L6-v2',  # 本地嵌入模型（通过 sentence-transformers）
            llm_backend="ollama",
            llm_model="llama3" 
        )
        print("✅ 系统初始化完成。")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 添加记忆
    print("\n📝 添加主权记忆...")
    content = "用户重视数据主权和本地处理。"
    try:
        # 注意：A-mem 会自动通过 LLM 生成标签和上下文
        memory_id = memory_system.add_note(
            content=content,
            tags=["主权", "隐私"],
            category="原则"
        )
        print(f"   记忆已存储，ID: {memory_id}")
    except Exception as e:
        print(f"❌ 存储记忆失败: {e}")
        return

    # 检索记忆
    print("\n🔍 检索记忆...")
    try:
        results = memory_system.search_agentic("主权", k=1)
        for res in results:
            print(f"   找到: {res['content']}")
            print(f"   标签: {res['tags']}")
            print(f"   上下文（LLM 生成）: {res.get('context', 'N/A')}")
    except Exception as e:
        print(f"❌ 检索失败: {e}")

if __name__ == "__main__":
    main()
