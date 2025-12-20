import { defineConfig } from 'vitepress'
import { glob } from 'glob'
import fs from 'fs'
import path from 'path'

// 自动读取 posts 目录下的文件
function getSidebar() {
  const postsDir = path.resolve(__dirname, '../posts')
  if (!fs.existsSync(postsDir)) return []
  
  const files = fs.readdirSync(postsDir)
    .filter(file => file.endsWith('.md') && file !== 'latest.md')
    .sort((a, b) => b.localeCompare(a)) // 按日期倒序

  return [
    {
      text: '🗓️ 往期日报',
      items: files.map(file => {
        const name = file.replace('.md', '')
        return { text: name, link: `/posts/${name}` }
      })
    }
  ]
}

export default defineConfig({
  // -----------------------------------------------------------------------
  // 🔴 重点修改这里！
  // 如果你的仓库链接是 github.com/cupide007/daily-news-bot
  // 那么这里必须填 '/daily-news-bot/' (前后都要有斜杠)
  // 如果你的仓库叫其他名字，请把中间的 daily-news-bot 改成你的仓库名
  // -----------------------------------------------------------------------
  base: '/daily-news-bot/', 
  
  title: "AI 舆情智库",
  description: "AI Driven Tech News",
  
  themeConfig: {
    siteTitle: 'Insight Pro 舆情',
    
    nav: [
      { text: '🔥 今日最新', link: '/posts/latest' },
      { text: 'GitHub', link: 'https://github.com/cupide007/daily-news-bot' }
    ],
    
    sidebar: getSidebar(),
    
    socialLinks: [
      { icon: 'github', link: 'https://github.com/cupide007/daily-news-bot' }
    ],
    
    footer: {
      message: 'Powered by Gemini & VitePress',
      copyright: 'Copyright © 2025 cupide007'
    }
  }
})
