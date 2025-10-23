"""
Jina AI 工具模块
提供 Embeddings 和 Rerank 功能
"""

import json

from loguru import logger

from .online_client import online_client


def generate_embeddings(
    text_input: str,
    model: str = "jina-embeddings-v3",
    task: str = "text-matching",
    encoding_format: str = "float"
) -> tuple[str, str]:
    """
    生成文本的 embeddings

    Args:
        text_input: 输入文本（每行一个文本）
        model: 模型名称
        task: 下游任务类型
        encoding_format: 输出数据类型

    Returns:
        (raw_output, markdown_output)
    """
    try:
        if not text_input or not text_input.strip():
            error_msg = "请输入文本"
            return error_msg, f"**Error:** {error_msg}"

        # 按行分割文本
        texts = [line.strip() for line in text_input.strip().split("\n") if line.strip()]

        if not texts:
            error_msg = "没有有效的文本输入"
            return error_msg, f"**Error:** {error_msg}"

        logger.info(f"生成 embeddings，模型: {model}, 文本数量: {len(texts)}, 任务: {task}, 编码: {encoding_format}")

        # 调用 embeddings API
        url = f"{online_client.base_url}/embeddings"
        payload = {"model": model, "input": texts}
        
        # 添加可选参数
        if task and task != "text-matching":
            payload["task"] = task
        
        if encoding_format and encoding_format != "float":
            payload["encoding_format"] = encoding_format

        response = online_client.session.post(url, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()

            # 格式化输出
            raw_output = json.dumps(result, indent=2, ensure_ascii=False)

            # Markdown 输出
            markdown_lines = ["# Embeddings 结果\n"]
            markdown_lines.append(f"**模型**: {model}\n")
            markdown_lines.append(f"**文本数量**: {len(texts)}\n")

            if "usage" in result:
                usage = result["usage"]
                markdown_lines.append(f"**Token 使用**: {usage.get('total_tokens', 'N/A')}\n")

            markdown_lines.append("\n## 向量维度\n")
            if result.get("data"):
                first_embedding = result["data"][0]["embedding"]
                markdown_lines.append(f"- 维度: {len(first_embedding)}\n")

            markdown_lines.append("\n## 输入文本\n")
            for i, text in enumerate(texts, 1):
                markdown_lines.append(f"{i}. {text}\n")

            markdown_output = "".join(markdown_lines)

            logger.info(f"Embeddings 生成成功，维度: {len(first_embedding)}")
            return raw_output, markdown_output
        else:
            error_msg = f"API 错误: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return error_msg, f"**Error:** {error_msg}"

    except Exception as e:
        error_msg = f"生成 embeddings 失败: {str(e)}"
        logger.error(error_msg)
        return error_msg, f"**Error:** {error_msg}"


def rerank_documents(query: str, documents: str, model: str = "jina-reranker-v2-base-multilingual", top_n: int = 3) -> tuple[str, str]:
    """
    对文档进行重排序

    Args:
        query: 查询文本
        documents: 文档列表（每行一个文档）
        model: 模型名称
        top_n: 返回前 N 个结果

    Returns:
        (raw_output, markdown_output)
    """
    try:
        if not query or not query.strip():
            error_msg = "请输入查询文本"
            return error_msg, f"**Error:** {error_msg}"

        if not documents or not documents.strip():
            error_msg = "请输入文档列表"
            return error_msg, f"**Error:** {error_msg}"

        # 按行分割文档
        doc_list = [line.strip() for line in documents.strip().split("\n") if line.strip()]

        if not doc_list:
            error_msg = "没有有效的文档输入"
            return error_msg, f"**Error:** {error_msg}"

        logger.info(f"Rerank 文档，模型: {model}, 查询: {query[:50]}..., 文档数量: {len(doc_list)}")

        # 调用 rerank API
        url = f"{online_client.base_url}/rerank"
        payload = {"model": model, "query": query, "documents": doc_list, "top_n": min(top_n, len(doc_list)), "return_documents": True}

        response = online_client.session.post(url, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()

            # 格式化输出
            raw_output = json.dumps(result, indent=2, ensure_ascii=False)

            # Markdown 输出
            markdown_lines = ["# Rerank 结果\n"]
            markdown_lines.append(f"**模型**: {model}\n")
            markdown_lines.append(f"**查询**: {query}\n")
            markdown_lines.append(f"**文档数量**: {len(doc_list)}\n")
            markdown_lines.append(f"**返回数量**: {top_n}\n")

            if "usage" in result:
                usage = result["usage"]
                markdown_lines.append(f"**Token 使用**: {usage.get('total_tokens', 'N/A')}\n")

            markdown_lines.append("\n## 排序结果\n")

            if result.get("results"):
                for i, item in enumerate(result["results"], 1):
                    score = item.get("relevance_score", 0)
                    index = item.get("index", -1)
                    
                    # 处理 document 字段，可能是字符串或字典
                    doc_field = item.get("document", "")
                    if isinstance(doc_field, dict):
                        doc_text = doc_field.get("text", "")
                    elif isinstance(doc_field, str):
                        doc_text = doc_field
                    else:
                        # 如果 document 字段不存在，使用原始文档
                        doc_text = doc_list[index] if 0 <= index < len(doc_list) else ""

                    markdown_lines.append(f"\n### {i}. 相关度分数: {score:.4f}\n")
                    markdown_lines.append(f"**原始索引**: {index}\n\n")
                    markdown_lines.append(f"{doc_text}\n")
                    markdown_lines.append("\n---\n")

            markdown_output = "".join(markdown_lines)

            logger.info(f"Rerank 成功，返回 {len(result.get('results', []))} 个结果")
            return raw_output, markdown_output
        else:
            error_msg = f"API 错误: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return error_msg, f"**Error:** {error_msg}"

    except Exception as e:
        error_msg = f"Rerank 失败: {str(e)}"
        logger.error(error_msg)
        return error_msg, f"**Error:** {error_msg}"


def search_web(
    query: str = "",
    url: str = "",
    respond_with: str = "default",
    with_images_summary: bool = False,
    with_links_summary: bool = False
) -> tuple[str, str]:
    """
    搜索网页或抓取特定 URL
    
    Args:
        query: 搜索查询文本
        url: 要抓取的 URL
        respond_with: 响应格式 (default, no-content, markdown, html, text, screenshot)
        with_images_summary: 是否包含图片摘要
        with_links_summary: 是否包含链接摘要
        
    Returns:
        (raw_output, markdown_output)
    """
    try:
        if not query and not url:
            error_msg = "请输入搜索查询或 URL"
            return error_msg, f"**Error:** {error_msg}"
        
        logger.info(f"搜索网页，查询: {query or 'N/A'}, URL: {url or 'N/A'}, 响应格式: {respond_with}")
        
        # 调用 search API
        api_url = f"{online_client.base_url}/search"
        params = {}
        if query:
            params["q"] = query
        if url:
            params["url"] = url
        
        # 设置自定义请求头
        headers = {"Accept": "application/json"}
        
        if respond_with and respond_with != "default":
            headers["X-Respond-With"] = respond_with
        
        if with_images_summary:
            headers["X-With-Images-Summary"] = "true"
        
        if with_links_summary:
            headers["X-With-Links-Summary"] = "true"
        
        response = online_client.session.get(api_url, params=params, headers=headers, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            
            # 格式化输出
            raw_output = json.dumps(result, indent=2, ensure_ascii=False)
            
            # Markdown 输出
            markdown_lines = ["# Search 结果\n"]
            if query:
                markdown_lines.append(f"**查询**: {query}\n")
            if url:
                markdown_lines.append(f"**URL**: {url}\n")
            
            if isinstance(result, dict):
                data = result.get("data", result)
                
                if isinstance(data, dict):
                    if data.get("title"):
                        markdown_lines.append(f"\n## {data['title']}\n")
                    if data.get("url"):
                        markdown_lines.append(f"**URL**: {data['url']}\n")
                    if data.get("description"):
                        markdown_lines.append(f"\n{data['description']}\n")
                    if data.get("content"):
                        content = data["content"][:500]
                        markdown_lines.append(f"\n### 内容预览\n\n{content}...\n")
                elif isinstance(data, list):
                    markdown_lines.append(f"\n## 搜索结果 ({len(data)} 条)\n")
                    for i, item in enumerate(data[:5], 1):
                        if isinstance(item, dict):
                            title = item.get("title", "无标题")
                            url = item.get("url", "")
                            markdown_lines.append(f"\n### {i}. {title}\n")
                            if url:
                                markdown_lines.append(f"URL: {url}\n")
            
            markdown_output = "".join(markdown_lines)
            
            logger.info("搜索成功")
            return raw_output, markdown_output
        else:
            error_msg = f"API 错误: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return error_msg, f"**Error:** {error_msg}"
            
    except Exception as e:
        error_msg = f"搜索失败: {str(e)}"
        logger.error(error_msg)
        return error_msg, f"**Error:** {error_msg}"


def read_url(
    url: str,
    engine: str = "direct",
    with_images_summary: bool = False,
    with_links_summary: bool = False
) -> tuple[str, str]:
    """
    读取 URL 内容并转换为 LLM 友好格式
    
    Args:
        url: 要读取的 URL
        engine: 引擎类型 (direct 或 browser)
        with_images_summary: 是否包含图片摘要
        with_links_summary: 是否包含链接摘要
        
    Returns:
        (raw_output, markdown_output)
    """
    try:
        if not url or not url.strip():
            error_msg = "请输入 URL"
            return error_msg, f"**Error:** {error_msg}"
        
        # 确保 URL 有协议
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        logger.info(f"读取 URL: {url}, 引擎: {engine}")
        
        # 调用 reader API
        api_url = f"{online_client.base_url}/reader/{url}"
        headers = {"Accept": "application/json"}
        
        if engine:
            headers["X-Engine"] = engine
        
        if with_images_summary:
            headers["X-With-Images-Summary"] = "true"
        
        if with_links_summary:
            headers["X-With-Links-Summary"] = "true"
        
        response = online_client.session.get(api_url, headers=headers, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            
            # 格式化输出
            raw_output = json.dumps(result, indent=2, ensure_ascii=False)
            
            # Markdown 输出
            markdown_lines = ["# Reader 结果\n"]
            markdown_lines.append(f"**URL**: {url}\n")
            markdown_lines.append(f"**引擎**: {engine}\n\n")
            
            if isinstance(result, dict):
                data = result.get("data", result)
                
                if isinstance(data, dict):
                    if data.get("title"):
                        markdown_lines.append(f"## {data['title']}\n\n")
                    if data.get("description"):
                        markdown_lines.append(f"**描述**: {data['description']}\n\n")
                    if data.get("content"):
                        content = data["content"]
                        # 限制内容长度以避免输出过长
                        if len(content) > 2000:
                            markdown_lines.append(f"### 内容 (前 2000 字符)\n\n{content[:2000]}...\n\n")
                            markdown_lines.append(f"*完整内容共 {len(content)} 字符，请查看 Raw Output*\n")
                        else:
                            markdown_lines.append(f"### 内容\n\n{content}\n")
            
            markdown_output = "".join(markdown_lines)
            
            logger.info(f"读取成功，内容长度: {len(result.get('data', {}).get('content', ''))}")
            return raw_output, markdown_output
        else:
            error_msg = f"API 错误: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return error_msg, f"**Error:** {error_msg}"
            
    except Exception as e:
        error_msg = f"读取 URL 失败: {str(e)}"
        logger.error(error_msg)
        return error_msg, f"**Error:** {error_msg}"
