import feedparser
import requests
import os
import shutil
from datetime import datetime
import pytz
import time
import random

# --- 🛠️ 配置区：在这里添加你想看的 RSS 源 ---
RSS_SOURCES = [
    {"name": "36氪", "url": "https://36kr.com/feed"},
    {"name": "少数派", "url": "https://sspai.com/feed"},
    # 想要加 IT之家？复制下面这行：
    {"name": "IT之家", "url": "https://www.ithome.com/rss/"},
    # 想要加 虎嗅？
    {"name": "虎嗅", "url": "https://www.huxiu.com/rss/0.xml"},
]
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- AI 调用封装 ---
def call_gemini(prompt):
    if not API_KEY:
        print("❌ 错误：未找到 GEMINI_API_KEY")
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    # 安全设置放行
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": safety_settings
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Network Error: {e}")
    return None

def generate_overview(titles):
    prompt = f"""
    请根据以下新闻标题，写一段150字左右的【科技舆情综述】。
    要求：语气专业、客观。不要分点，写成一段连贯的文字。
    标题列表：
    {titles}
    """
    return call_gemini(prompt)

def generate_summary(content):
    prompt = f"""
    请对这条新闻进行极简总结（50字以内），并提取1个核心标签。
    格式要求：摘要内容|标签
    新闻内容：
    {content[:800]}
    """
    return call_gemini(prompt)

def main():
    # 1. 准备目录
    posts_dir = "docs/posts"
    if not os.path.exists(posts_dir): os.makedirs(posts_dir)

    tz = pytz.timezone('Asia/Shanghai')
    today = datetime.now(tz).strftime("%Y-%m-%d")
    now_time = datetime.now(tz).strftime("%H:%M")

    # 2. 循环抓取所有源
    all_entries = []
    
    print(f"🚀 开始抓取 {len(RSS_SOURCES)} 个源...")
    
    for source in RSS_SOURCES:
        try:
            print(f"   正在抓取: {source['name']}...")
            feed = feedparser.parse(source['url'])
            if not feed.entries: continue
            
            # 只取每个源的前 5 条，防止处理时间过长
            for entry in feed.entries[:5]:
                # 把来源名字塞进 entry 对象里，后面要用
                entry['source_name'] = source['name']
                all_entries.append(entry)
        except Exception as e:
            print(f"   ❌ {source['name']} 抓取失败: {e}")

    # 3. 混合与排序
    # 尝试按发布时间倒序排列 (如果 RSS 里有标准时间字段)
    # 如果没有时间字段，就随机打乱一点，显得比较丰富
    try:
        all_entries.sort(key=lambda x: x.published_parsed if 'published_parsed' in x and x.published_parsed else time.localtime(), reverse=True)
    except:
        random.shuffle(all_entries)

    # 最终只取前 12 条进行 AI 处理 (控制成本和时间)
    final_entries = all_entries[:12]
    titles_list = [e.title for e in final_entries]

    # 4. 生成宏观综述
    print("🤖 正在生成宏观综述...")
    overview_text = generate_overview("\n".join(titles_list))
    if not overview_text: overview_text = "今日暂无综述。"
    overview_text = overview_text.replace("\n", "").replace('"', "'")

    # 5. 拼接 Markdown (保持 Plan A 的单行 HTML 风格)
    md = f"# 📅 舆情日报 {today}\n\n"
    md += f'<div class="update-time">更新于北京时间 {now_time}</div>\n\n'
    md += f'<div class="daily-overview"><h3>🛡️ 全网舆情综述</h3><p>{overview_text}</p></div>\n\n'
    md += '<div class="news-list">\n\n'

    # 6. 处理每条新闻
    for i, entry in enumerate(final_entries):
        source_name = entry.get('source_name', '资讯')
        print(f"[{i+1}/{len(final_entries)}] 处理 [{source_name}]: {entry.title}")
        
        content = entry.summary if 'summary' in entry else entry.title
        ai_res = generate_summary(content)
        
        summary = "AI 暂未生成摘要"
        tag = "热点"
        
        if ai_res and "|" in ai_res:
            parts = ai_res.split("|")
            summary = parts[0].strip().replace("\n", "")
            if len(parts) > 1: tag = parts[1].strip()
        elif ai_res:
            summary = ai_res.replace("\n", "")

        # 生成卡片 (单行 HTML，防止缩进错误)
        # 注意：这里把 '36Kr' 换成了动态的 {source_name}
        card_html = f'<div class="news-card"><h4><a href="{entry.link}" target="_blank">{entry.title}</a></h4><div class="summary">{summary}</div><div class="news-meta"><span class="tag-pill">{tag}</span><span class="source-name">{source_name}</span></div></div>'
        
        md += card_html + "\n\n"
        time.sleep(1) # 休息一下，防限流

    md += '</div>\n'

    # 7. 保存
    file_path = os.path.join(posts_dir, f"{today}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md)
    shutil.copy(file_path, os.path.join(posts_dir, "latest.md"))
    print(f"✅ 完成！共生成 {len(final_entries)} 条简报")

if __name__ == "__main__":
    main()
