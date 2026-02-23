from typing import Dict, Optional, Literal, Any
import os
import json
from abc import ABC, abstractmethod
from litellm import completion

class BaseLLMController(ABC):
    """
    抽象基类，用于定义与语言模型（LLM）交互的接口。
    """
    @abstractmethod
    def get_completion(self, prompt: str) -> str:
        """
        获取语言模型的补全结果。
        
        参数：
            prompt (str): 输入的提示文本。
        返回：
            str: 补全的文本。
        """
        pass

class OpenAIController(BaseLLMController):
    """
    OpenAI 的语言模型控制器。
    """
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        """
        初始化 OpenAI 控制器。
        
        参数：
            model (str): 使用的模型名称，默认为 "gpt-4"。
            api_key (Optional[str]): OpenAI 的 API 密钥。
        """
        try:
            from openai import OpenAI
            self.model = model
            if api_key is None:
                api_key = os.getenv('OPENAI_API_KEY')
            if api_key is None:
                raise ValueError("未找到 OpenAI API 密钥，请设置 OPENAI_API_KEY 环境变量。")
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("未找到 OpenAI 包，请使用以下命令安装：pip install openai")
    
    def get_completion(self, prompt: str, response_format: dict, temperature: float = 0.7) -> str:
        """
        获取语言模型的补全结果。
        
        参数：
            prompt (str): 输入的提示文本。
            response_format (dict): 响应格式。
            temperature (float): 生成文本的随机性，默认为 0.7。
        返回：
            str: 补全的文本。
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You must respond with a JSON object."},
                {"role": "user", "content": prompt}
            ],
            response_format=response_format,
            temperature=temperature,
            max_tokens=1000
        )
        return response.choices[0].message.content

class OllamaController(BaseLLMController):
    """
    Ollama 的语言模型控制器。
    """
    def __init__(self, model: str = "llama2"):
        """
        初始化 Ollama 控制器。
        
        参数：
            model (str): 使用的模型名称，默认为 "llama2"。
        """
        from ollama import chat
        self.model = model
    
    def _generate_empty_value(self, schema_type: str, schema_items: dict = None) -> Any:
        """
        根据模式类型生成空值。
        
        参数：
            schema_type (str): 模式的类型（如 "array"、"string"、"object"）。
            schema_items (dict): 模式的具体项，默认为 None。
        返回：
            Any: 生成的空值。
        """
        if schema_type == "array":
            return []
        elif schema_type == "string":
            return ""
        elif schema_type == "object":
            return {}
        elif schema_type == "number":
            return 0
        elif schema_type == "boolean":
            return False
        return None

    def _generate_empty_response(self, response_format: dict) -> dict:
        """
        生成空响应。
        
        参数：
            response_format (dict): 响应格式。
        返回：
            dict: 生成的空响应。
        """
        if "json_schema" not in response_format:
            return {}
            
        schema = response_format["json_schema"]["schema"]
        result = {}
        
        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                result[prop_name] = self._generate_empty_value(prop_schema["type"], 
                                                            prop_schema.get("items"))
        
        return result

    def get_completion(self, prompt: str, response_format: dict, temperature: float = 0.7) -> str:
        # Allow exceptions (like ConnectionError) to bubble up for better debugging
        response = completion(
            model="ollama_chat/{}".format(self.model),
            messages=[
                {"role": "system", "content": "You must respond with a JSON object."},
                {"role": "user", "content": prompt}
            ],
            response_format=response_format,
        )
        return response.choices[0].message.content

class LLMController:
    """LLM-based controller for memory metadata generation"""
    def __init__(self, 
                 backend: Literal["openai", "ollama"] = "openai",
                 model: str = "gpt-4", 
                 api_key: Optional[str] = None):
        if backend == "openai":
            self.llm = OpenAIController(model, api_key)
        elif backend == "ollama":
            self.llm = OllamaController(model)
        else:
            raise ValueError("Backend must be one of: 'openai', 'ollama'")
            
    def get_completion(self, prompt: str, response_format: dict = None, temperature: float = 0.7) -> str:
        return self.llm.get_completion(prompt, response_format, temperature)
