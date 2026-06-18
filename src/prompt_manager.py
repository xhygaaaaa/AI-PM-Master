"""Prompt 版本管理 - 保存、加载、对比不同版本的 Prompt"""
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

import config


class PromptManager:
    """Prompt 版本管理器"""

    def __init__(self):
        """初始化 Prompt 管理器"""
        self.prompts_dir = config.PROMPTS_DIR
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def save_prompt(
        self,
        version_name: str,
        system_prompt: str,
        user_prompt_template: str,
        description: str = "",
        metadata: Dict = None
    ) -> bool:
        """
        保存一个 Prompt 版本

        Args:
            version_name: 版本名称（如 "v1", "v2_stricter"）
            system_prompt: 系统提示词
            user_prompt_template: 用户提示词模板
            description: 版本描述
            metadata: 额外的元数据（如修改原因、预期效果）

        Returns:
            是否保存成功
        """
        # 构建版本数据
        prompt_data = {
            "version_name": version_name,
            "system_prompt": system_prompt,
            "user_prompt_template": user_prompt_template,
            "description": description,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }

        # 保存到文件
        file_path = self.prompts_dir / f"{version_name}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(prompt_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Prompt 版本已保存：{version_name}")
            return True
        except Exception as e:
            print(f"❌ 保存失败：{e}")
            return False

    def load_prompt(self, version_name: str) -> Optional[Dict]:
        """
        加载一个 Prompt 版本

        Args:
            version_name: 版本名称

        Returns:
            Prompt 数据字典，如果不存在返回 None
        """
        file_path = self.prompts_dir / f"{version_name}.json"
        if not file_path.exists():
            print(f"⚠️  版本不存在：{version_name}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                prompt_data = json.load(f)
            return prompt_data
        except Exception as e:
            print(f"❌ 加载失败：{e}")
            return None

    def list_prompts(self) -> List[Dict]:
        """
        列出所有已保存的 Prompt 版本

        Returns:
            版本列表，每个元素包含基本信息
        """
        prompts = []
        for file_path in self.prompts_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                prompts.append({
                    "version_name": data.get("version_name"),
                    "description": data.get("description", ""),
                    "created_at": data.get("created_at", ""),
                })
            except Exception as e:
                print(f"⚠️  读取文件失败 {file_path}: {e}")
                continue

        # 按创建时间排序
        prompts.sort(key=lambda x: x["created_at"], reverse=True)
        return prompts

    def delete_prompt(self, version_name: str) -> bool:
        """
        删除一个 Prompt 版本

        Args:
            version_name: 版本名称

        Returns:
            是否删除成功
        """
        file_path = self.prompts_dir / f"{version_name}.json"
        if not file_path.exists():
            print(f"⚠️  版本不存在：{version_name}")
            return False

        try:
            file_path.unlink()
            print(f"✅ 已删除版本：{version_name}")
            return True
        except Exception as e:
            print(f"❌ 删除失败：{e}")
            return False

    def compare_prompts(self, version1: str, version2: str) -> Dict:
        """
        对比两个 Prompt 版本

        Args:
            version1: 版本 1 名称
            version2: 版本 2 名称

        Returns:
            对比结果字典
        """
        data1 = self.load_prompt(version1)
        data2 = self.load_prompt(version2)

        if not data1 or not data2:
            return {"error": "版本不存在"}

        # 简单的文本差异统计
        sys1 = data1["system_prompt"]
        sys2 = data2["system_prompt"]
        user1 = data1["user_prompt_template"]
        user2 = data2["user_prompt_template"]

        return {
            "version1": version1,
            "version2": version2,
            "system_prompt_changed": sys1 != sys2,
            "user_prompt_changed": user1 != user2,
            "system_prompt_length_diff": len(sys2) - len(sys1),
            "user_prompt_length_diff": len(user2) - len(user1),
            "data1": data1,
            "data2": data2,
        }

    def initialize_default_prompts(self):
        """初始化默认的 Prompt 版本（如果不存在）"""
        # v1：基础版本
        if not (self.prompts_dir / "v1.json").exists():
            self.save_prompt(
                version_name="v1",
                system_prompt=config.DEFAULT_SYSTEM_PROMPT,
                user_prompt_template=config.USER_PROMPT_TEMPLATE,
                description="基础版本，标准的 RAG 问答 Prompt",
                metadata={
                    "适用场景": "通用知识问答",
                    "特点": "平衡的约束和灵活性",
                }
            )

        # v2：严格版本（更强调不编造）
        if not (self.prompts_dir / "v2_strict.json").exists():
            strict_system = """你是一个极其严谨的智能问答助手。

你的职责：
1. **只能**根据提供的参考文档回答问题
2. 如果文档中没有明确提到，必须回答"文档中未找到相关信息"
3. 绝对不能推测、猜测、补充任何文档中没有的内容
4. 引用原文时，尽量使用原文的表述，不要改写

你不能：
1. 根据常识推断
2. 编造任何细节
3. 回答文档范围外的问题
4. 给出个人意见或建议
"""
            self.save_prompt(
                version_name="v2_strict",
                system_prompt=strict_system,
                user_prompt_template=config.USER_PROMPT_TEMPLATE,
                description="严格版本，极力避免幻觉，宁可拒答也不编造",
                metadata={
                    "适用场景": "高风险领域（医疗、法律、金融）",
                    "特点": "极低的幻觉率，可能拒答率较高",
                    "改进点": "加强了'不能编造'的约束",
                }
            )

        # v3：友好版本（更注重用户体验）
        if not (self.prompts_dir / "v3_friendly.json").exists():
            friendly_system = """你是一个友好、专业的智能问答助手。

你的职责：
1. 根据参考文档回答用户问题，解答要清晰易懂
2. 如果文档中没有相关信息，礼貌地告知并引导用户换个问题
3. 回答要有条理，可以使用编号列表
4. 适当使用 Emoji 让回答更生动（但不要过度）

回答风格：
- 先给结论，再给细节
- 复杂问题可以分步骤说明
- 专业术语要适当解释

你不能：
- 编造文档中不存在的信息
- 提供医疗、法律等专业建议
"""
            self.save_prompt(
                version_name="v3_friendly",
                system_prompt=friendly_system,
                user_prompt_template=config.USER_PROMPT_TEMPLATE,
                description="友好版本，注重用户体验和可读性",
                metadata={
                    "适用场景": "C 端产品，注重用户体验",
                    "特点": "回答更友好、更有结构",
                    "改进点": "增加了回答格式的引导",
                }
            )

        print("✅ 默认 Prompt 版本已初始化")
