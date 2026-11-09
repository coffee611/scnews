import os
import re
import requests
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

KEYWORDS = [
    "AI 반도체", "삼성전자", "SK하이닉스", "HBM", 
    "D램", "낸드", "파운드리", "디스플레이", "데이터센터"
]

# 국내 주요 경제·일간지
DOMESTIC_DOMAINS = "(site:hankyung.com OR site:mk.co.kr OR site:sedaily.com OR site:mt.co.kr OR site:edaily.co.kr OR site:etnews.com OR site:chosun.com OR site:joongang.co.kr OR site:donga.com OR site:hani.co.kr OR site:khan.co.kr OR site:hankookilbo.com OR site:yna.co.kr)"
DOMESTIC_SOURCES = ["한국경제", "매일경제", "서울경제", "머니투데이", "이데일리", "전자신문", "조선일보", "중앙일보", "동아일보", "한겨레", "경향신문", "한국일보", "연합뉴스"]

# 해외 외신 및 IT 전문지
OVERSEAS_DOMAINS = "(site:reuters.com OR site:bloomberg.com OR site:cnbc.com OR site:ft.com OR site:asia.nikkei.com OR site:trendforce.com OR site:digitimes.com)"
OVERSEAS_SOURCES = ["Reuters", "Bloomberg", "CNBC", "Financial Times", "Nikkei", "TrendForce", "DigiTimes"]

def clean_summary(raw_html):
    if not raw_html:
        return "핵심 요약 정보를 불러오지 못했습니다."
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text()
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > 120:
        text = text[:120] + "..."
    return text

def fetch_article(keyword, domains, sources):
    query = f"{keyword} {domains} when:1d"
    url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    
    if feed.entries:
        entry = feed.entries[0]
        return {
            "title": entry.title,
            "link": entry.link,
            "source": entry.source.title if 'source' in entry else "주요 매체",
            "summary": clean_summary(entry.get('summary', ''))
        }
    
    fallback_query = f"{keyword} when:1d"
    fallback_url = f"https://news.google.com/rss/search?q={fallback_query}&hl=ko&gl=KR&ceid=KR:ko"
    fallback_feed = feedparser.parse(fallback_url)
    
    for entry in fallback_feed.entries:
        source_title = entry.source.title if 'source' in entry else ""
        if any(src.lower() in source_title.lower() for src in sources):
            return {
                "title": entry.title,
                "link": entry.link,
                "source": source_title,
                "summary": clean_summary(entry.get('summary', ''))
            }
    return None

def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("토큰 설정 오류")
        return

    today_str = datetime.now().strftime("%Y년 %m월 %d일")
    message = f"📢 *[{today_str} 사업개발팀 반도체 조간 브리핑]*\n"
    message += "━━━━━━━━━━━━━━━━━━━\n\n"
    
    seen_links = set()
    
    # 국내 뉴스 파트
    message += "🇰🇷 *[국내 주요 경제 및 일간지]*\n"
    dom_count = 0
    for kw in KEYWORDS:
        article = fetch_article(kw, DOMESTIC_DOMAINS, DOMESTIC_SOURCES)
        if article and article['link'] not in seen_links:
            seen_links.add(article['link'])
            dom_count += 1
            message += f"• *[{kw}]* [{article['title']}]({article['link']})\n"
            message += f"  📝 _{article['summary']}_\n"
            message += f"  └ 출처: {article['source']}\n\n"
            
    if dom_count == 0:
        message += "• 수집된 국내 기사가 없습니다.\n\n"
    
    # 해외 외신 파트
    message += "🌐 *[해외 외신 및 전문 매체]*\n"
    over_count = 0
    for kw in KEYWORDS:
        article = fetch_article(kw, OVERSEAS_DOMAINS, OVERSEAS_SOURCES)
        if article and article['link'] not in seen_links:
            seen_links.add(article['link'])
            over_count += 1
            message += f"• *[{kw}]* [{article['title']}]({article['link']})\n"
            message += f"  📝 _{article['summary']}_\n"
            message += f"  └ 출처: {article['source']}\n\n"
            
    if over_count == 0:
        message += "• 수집된 해외 기사가 없습니다.\n\n"
        
    message += "━━━━━━━━━━━━━━━━━━━\n"
    message += "💡 오늘도 성공적인 하루 보내세요, 사업개발팀 화이팅!"

    send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(send_url, json={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    })

if __name__ == "__main__":
    main()
