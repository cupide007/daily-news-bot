import feedparser
import requests
import os
from datetime import datetime
import pytz

# --- 配置 ---
RSS_URL = "https://36kr.com/feed" 
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- HTML 模板 (内含 CSS 样式) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日 AI 简报</title>
    <style>
        :root { --bg: #f6f6ef; --card-bg: #fff; --text: #333; --accent: #ff6600; }
        @media (prefers-color-scheme: dark) {
            :root { --bg: #1a1a1a; --card-bg: #2d2d2d; --text: #e0e0e0; --accent: #ff8533; }
        }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; line-height: 1.6; }
        .container { max-width: 800px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 2px solid var(--accent); }
        h1 { margin: 0; color: var(--accent); }
        .date { color: #888; font-size: 0.9em; }
        .card { background: var(--card-bg); padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: transform 0.2s; }
        .card:hover { transform: translateY(-2px); }
        .card h2 { margin-top: 0; font-size: 1.2em; }
        .card a { text-decoration: none; color: inherit; }
        .card a:hover { color: var(--accent); }
        .summary { color: var(--text); opacity: 0.9; margin: 10px 0; font-size: 0.95em; }
        .meta { font-size: 0.8em; color: #888; margin-top: 10px; display: flex; justify-content: space-between; }
        .tag { background: var(--accent); color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; opacity: 0.8; }
        footer { text-align: center; margin-top: 40px; font-size: 0.8em; color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📰 Daily News AI</h1>
            <p class="date">更新时间: {update_time}</p>
        </header>
        
        {content_list}
        
        <footer>
            Powered by GitHub Actions & Gemini
        </footer>
    </div>
</body>
</html>
"""

def summarize_with_ai(content):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    # 提示词微调：要求返回纯文本，不要 markdown 格式
    prompt = f"请阅读以下新闻，生成一段80字以内的中文摘要。然后提炼1个核心关键词。格式要求：摘要内容|关键词\n\n内容：{content[:1500]}"
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200: return "摘要生成失败|Error"
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "AI 暂时无法响应|N/A"

def main():
    feed = feedparser.parse(RSS_URL)
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    
    cards_html = ""
    
    # 只取前 8 条，避免运行太久
    for entry in feed.entries[:8]:
        print(f"处理: {entry.title}")
        content = entry.summary if 'summary' in entry else entry.title
        
        # AI 处理
        ai_result = summarize_with_ai(content)
        # 简单的容错处理
        if "|" in ai_result:
            summary, tag = ai_result.split("|", 1)
        else:
            summary, tag = ai_result, "News"
            
        # 拼接 HTML 卡片
        cards_html += f"""
        <div class="card">
            <h2><a href="{entry.link}" target="_blank">{entry.title}</a></h2>
            <div class="summary">{summary}</div>
            <div class="meta">
                <span>{entry.published[:16] if hasattr(entry, 'published') else ''}</span>
                <span class="tag">{tag.strip()}</span>
            </div>
        </div>
        """
    
    # 生成最终 HTML
    final_html = HTML_TEMPLATE.format(update_time=now, content_list=cards_html)
    
    # 写入 index.html (这是 GitHub Pages 的默认入口)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("网页生成完毕！")

if __name__ == "__main__":
    main()
