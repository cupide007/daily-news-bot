import feedparser
import requests
import os
import shutil
from datetime import datetime
import pytz

# --- 配置 ---
RSS_URL = "https://36kr.com/feed" 
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- AI 处理函数 ---
def summarize_with_ai(content):
    # 使用 Gemini Flash 模型
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemma-3-4b:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # 提示词：要求返回 "摘要|标签" 的格式
    prompt = f"请阅读以下新闻，用中文写一段摘要（50-80字），并提取1个标签。格式：摘要|标签\n\n内容：{content[:1500]}"
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200: 
            print(f"API Error: {response.text}")
            return "AI生成失败|Error"
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Request Error: {e}")
        return "AI未响应|Error"

# --- 主逻辑 ---
def main():
    # 1. 准备 docs/posts 目录 (VitePress 的文章目录)
    posts_dir = "docs/posts"
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)

    # 2. 获取时间
    tz = pytz.timezone('Asia/Shanghai')
    today_str = datetime.now(tz).strftime("%Y-%m-%d")
    current_time = datetime.now(tz).strftime("%H:%M")
    
    print(f"开始抓取 RSS: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("❌ 未获取到 RSS 内容，请检查网络或源地址")
        return

    # 3. 生成 Markdown 内容头部
    md_content = f"# 📅 每日简报 {today_str}\n\n"
    md_content += f"> 更新时间：{current_time}\n\n"
    
    # 4. 循环处理前 10 条新闻
    for entry in feed.entries[:10]: 
        title = entry.title
        link = entry.link
        print(f"正在处理: {title}")
        
        content = entry.summary if 'summary' in entry else title
        
        # 调用 AI
        res = summarize_with_ai(content)
        
        # 解析返回结果 (容错处理)
        if "|" in res:
            summary, tag = res.split("|", 1)
        else:
            summary, tag = res, "News"
            
        # 拼接 Markdown (VitePress 格式)
        md_content += f"### [{title}]({link})\n"
        md_content += f"- **标签**: `{tag.strip()}`\n"
        md_content += f"- **摘要**: {summary}\n\n"
        md_content += "---\n\n"

    # 5. 保存文件：docs/posts/yyyy-mm-dd.md
    filename = os.path.join(posts_dir, f"{today_str}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    # 6. 复制一份为 latest.md (用于首页“开始阅读”按钮)
    shutil.copy(filename, os.path.join(posts_dir, "latest.md"))
    
    print(f"✅ 成功生成文件: {filename}")

if __name__ == "__main__":
    main()
