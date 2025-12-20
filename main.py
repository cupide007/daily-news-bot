import feedparser
import requests
import json
import os
from datetime import datetime

# --- 配置部分 ---
# 这里换成你想抓取的 RSS 源，例如 36氪、少数派等
RSS_URL = "https://36kr.com/feed" 
API_KEY = os.environ.get("GEMINI_API_KEY") # 从 GitHub Secrets 获取

# --- AI 处理函数 (调用 Gemini) ---
def summarize_with_ai(content):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # 提示词：你可以修改这里来调整 AI 的语气
    prompt = f"请用中文简要总结这篇新闻，控制在100字以内，并列出3个相关标签。\n\n内容：{content[:2000]}" 
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"AI Error: {e}")
        return "AI 总结失败，请查看原文。"

# --- 主逻辑 ---
def main():
    # 1. 获取 RSS
    feed = feedparser.parse(RSS_URL)
    
    today = datetime.now().strftime("%Y-%m-%d")
    markdown_content = f"# 📅 每日新闻简报 ({today})\n\n"

    # 2. 处理前 5 条新闻 (为了节省时间演示)
    for entry in feed.entries[:5]: 
        title = entry.title
        link = entry.link
        # 有些 RSS 的正文在 summary 里，有些在 content 里
        content = entry.summary if 'summary' in entry else title 
        
        print(f"正在处理: {title}...")
        
        # 3. 调用 AI
        ai_summary = summarize_with_ai(content)
        
        # 4. 拼装 Markdown
        markdown_content += f"## {title}\n\n"
        markdown_content += f"{ai_summary}\n\n"
        markdown_content += f"[🔗 阅读原文]({link})\n\n---\n\n"

    # 5. 写入文件 (覆盖 README.md 或者生成新文件)
    # 这里我们直接更新 README.md，这样你打开仓库首页就能看到
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    print("更新完成！")

if __name__ == "__main__":
    main()
