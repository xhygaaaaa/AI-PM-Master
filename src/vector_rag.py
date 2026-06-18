"""语义检索引擎 - 基于 Embedding + FAISS 向量数据库"""
import os
import pickle
from typing import List, Tuple, Dict
from pathlib import Path

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

import config


class VectorRAG:
    """基于向量检索的 RAG 引擎"""

    def __init__(self, documents: Dict[str, str] = None):
        """
        初始化向量检索引擎

        Args:
            documents: {文档名称: 文档内容} 的字典
        """
        print("🔄 正在加载 Embedding 模型...")
        # 加载 Embedding 模型（首次会自动下载，约 118MB）
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        print(f"✅ Embedding 模型加载完成：{config.EMBEDDING_MODEL}")

        # 文档存储
        self.documents = documents or {}
        self.doc_chunks = {}  # {文档名称: [段落列表]}
        self.chunk_metadata = []  # [(文档名称, 段落索引), ...]

        # FAISS 索引
        self.index = None
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()

        # 如果提供了文档，立即构建索引
        if documents:
            self._build_index()

    def _split_document(self, content: str) -> List[str]:
        """
        将文档切分成段落

        切分策略：
        1. 按双换行符切分（段落分隔）
        2. 过滤掉过短的段落（<20 字）
        3. 每个段落最长 500 字（避免超出 Embedding 模型限制）

        Args:
            content: 文档内容

        Returns:
            段落列表
        """
        # 按双换行或单换行切分
        paragraphs = content.split('\n\n')
        if len(paragraphs) <= 1:
            paragraphs = content.split('\n')

        chunks = []
        for para in paragraphs:
            para = para.strip()
            # 过滤过短的段落
            if len(para) < 20:
                continue

            # 如果段落过长，按句子切分
            if len(para) > 500:
                sentences = para.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > 500:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += sentence
                if current_chunk:
                    chunks.append(current_chunk.strip())
            else:
                chunks.append(para)

        return chunks

    def _build_index(self):
        """构建 FAISS 向量索引"""
        print("🔄 正在构建向量索引...")

        # 1. 切分文档
        all_chunks = []
        for doc_name, content in self.documents.items():
            chunks = self._split_document(content)
            self.doc_chunks[doc_name] = chunks

            # 记录每个 chunk 的元数据（来自哪个文档）
            for idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                self.chunk_metadata.append((doc_name, idx))

        if not all_chunks:
            print("⚠️  警告：没有文档可索引")
            return

        print(f"📄 共切分出 {len(all_chunks)} 个段落")

        # 2. 生成 Embedding 向量
        print("🔄 正在生成 Embedding 向量...")
        embeddings = self.embedding_model.encode(
            all_chunks,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        embeddings = embeddings.astype('float32')  # FAISS 需要 float32

        # 3. 创建 FAISS 索引
        # 使用 IndexFlatIP（内积，适合归一化后的向量）
        # 归一化向量后，内积 = 余弦相似度
        faiss.normalize_L2(embeddings)  # L2 归一化
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings)

        print(f"✅ 向量索引构建完成，共 {self.index.ntotal} 个向量")

    def add_documents(self, documents: Dict[str, str]):
        """
        添加新文档并重建索引

        Args:
            documents: {文档名称: 文档内容}
        """
        self.documents.update(documents)
        self._build_index()

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """
        检索最相关的文档段落

        Args:
            query: 用户问题
            top_k: 返回前 k 个结果

        Returns:
            [(文档名称, 段落内容, 相似度得分), ...]
            相似度得分范围 [0, 1]，越大越相似
        """
        if self.index is None or self.index.ntotal == 0:
            print("⚠️  警告：向量索引为空，无法检索")
            return []

        # 1. 查询向量化
        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True
        ).astype('float32')
        faiss.normalize_L2(query_embedding)  # 归一化

        # 2. FAISS 检索
        # top_k 不能超过索引中的向量总数
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_embedding, k)

        # 3. 组装结果
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS 返回 -1 表示无结果
                continue

            doc_name, chunk_idx = self.chunk_metadata[idx]
            chunk_content = self.doc_chunks[doc_name][chunk_idx]

            # 相似度得分（内积，范围约 [0, 1]）
            results.append((doc_name, chunk_content, float(score)))

        return results

    def save_index(self, save_dir: str = None):
        """
        保存向量索引到磁盘（避免重复构建）

        Args:
            save_dir: 保存目录，默认为 data/ 目录
        """
        if save_dir is None:
            save_dir = config.DATA_DIR

        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        # 保存 FAISS 索引
        index_path = save_dir / "faiss_index.bin"
        faiss.write_index(self.index, str(index_path))

        # 保存元数据
        metadata_path = save_dir / "index_metadata.pkl"
        metadata = {
            "doc_chunks": self.doc_chunks,
            "chunk_metadata": self.chunk_metadata,
            "documents": self.documents,
        }
        with open(metadata_path, "wb") as f:
            pickle.dump(metadata, f)

        print(f"✅ 索引已保存到 {save_dir}")

    def load_index(self, load_dir: str = None):
        """
        从磁盘加载向量索引

        Args:
            load_dir: 加载目录，默认为 data/ 目录
        """
        if load_dir is None:
            load_dir = config.DATA_DIR

        load_dir = Path(load_dir)

        # 加载 FAISS 索引
        index_path = load_dir / "faiss_index.bin"
        if not index_path.exists():
            print(f"⚠️  索引文件不存在：{index_path}")
            return False

        self.index = faiss.read_index(str(index_path))

        # 加载元数据
        metadata_path = load_dir / "index_metadata.pkl"
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)

        self.doc_chunks = metadata["doc_chunks"]
        self.chunk_metadata = metadata["chunk_metadata"]
        self.documents = metadata["documents"]

        print(f"✅ 索引已从 {load_dir} 加载，共 {self.index.ntotal} 个向量")
        return True


def load_knowledge_base() -> VectorRAG:
    """
    加载知识库并构建向量索引

    Returns:
        VectorRAG 实例
    """
    # 检查是否已有保存的索引
    rag = VectorRAG()
    if rag.load_index():
        print("✅ 使用已保存的向量索引")
        return rag

    # 否则，加载文档并重新构建
    print("🔄 首次运行，正在构建向量索引...")
    documents = {}

    # 从 knowledge_base 目录加载所有 .txt 文件
    kb_dir = config.KNOWLEDGE_BASE_DIR
    if not kb_dir.exists():
        print(f"⚠️  知识库目录不存在：{kb_dir}")
        return rag

    for file_path in kb_dir.glob("*.txt"):
        doc_name = file_path.stem  # 文件名（不含扩展名）
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        documents[doc_name] = content
        print(f"📄 加载文档：{doc_name}")

    if not documents:
        print("⚠️  知识库为空，请在 data/knowledge_base/ 目录下添加 .txt 文件")
        return rag

    # 构建索引
    rag.add_documents(documents)

    # 保存索引
    rag.save_index()

    return rag
