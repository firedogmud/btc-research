# BTC Research Aggregator

每天自動抓取 10 個 BTC macro + mining 研究來源，過濾後推送到 Notion。

## Setup
1. Import 這個 repo 到你的 GitHub
2. Settings → Secrets → Actions → 加兩個 secret:
   - NOTION_API_KEY
   - NOTION_DATABASE_ID
3. Actions tab → Daily BTC Research Fetch → Run workflow
4. 之後每天 HKT 08:00 自動執行
