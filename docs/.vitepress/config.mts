import { defineConfig } from 'vitepress'
import { glob } from 'glob'
import fs from 'fs'
import path from 'path'

// 自动扫描 posts 目录下的文件生成侧边栏
// 这样你不需要手动改配置，Python 生成新文件后，这里会自动读取
function getSidebar() {
  const postsDir = path.resolve(__dirname, '../posts')
  if (!fs.existsSync(postsDir)) return []
  
  const files = fs.readdirSync(postsDir)
    .filter(file => file.endsWith('.md') && file !== 'latest.md')
    .sort((a, b) => b.localeCompare(a)) // 按文件名倒序排列（最新的在上面）

  return [
    {
      text: '每日简报',
      items: files.map(file => {
        const name = file.replace('.md', '')
        return { text: name, link: `/posts/${name}` }
      })
    }
  ]
}

export default defineConfig({
  title: "Daily News AI",
  description: "AI Daily News Aggregator",
  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '关于', link: 'https://github.com/你的用户名/daily-news-bot' }
    ],
    sidebar: getSidebar(),
    socialLinks: [
      { icon: 'github', link: 'https://github.com/你的用户名/daily-news-bot' }
    ]
  }
})

