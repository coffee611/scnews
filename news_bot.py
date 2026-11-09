import os
import re
import requests
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

KEYWORDS = [
    "AI 반도체", "삼성전자", "SK하이닉스", "HBM", 
    "D램", "낸드", "파운드리", "디스플레이", "데이터센터"
]

# 타겟 언론사 이름 키워드 리스트 (이 중 하나의 단어가 출처에 포함되면 통과)
DOMESTIC_SOURCES = ["한국경제", "매일경제", "서울경제", "머니투데이", "이데일리", "전자신문", "조선일보", "중앙일보", "동아일보", "한겨레", "경향신문", "한국일보", "연합뉴스"]
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

def fetch_articles_by_sources(keyword, target_sources):
    """site 연산자 없이 키워드로 검색한 뒤, 지정된 언론사 리스트에 매칭되는 기사들을 수집"""
    encoded_query = quote(f"{keyword} when:1d")
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    
    matched_articles = []
    
    for entry in feed.entries:
        source_title = entry.source.title if 'source' in entry else ""
        # 언론사 이름이 일치하는지 확인
        if any(src.lower() in source_title.lower() for src in target_sources):
            matched_articles.append({
                "title": entry.title,
                "link": entry.link,
                "source": source_title,
                "summary": clean_summary(entry.get('summary', ''))
            })
            
    return matched_articles

def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("토큰 설정 오류")
        return

    today_str = datetime.now().strftime("%Y년 %m월 %d일")
    message = f"📢 *[{today_str} 사업개발팀 반도체 조간 브리핑]*\n"
    message += "━━━━━━━━━━━━━━━━━━━\n\n"
    
    seen_links = set()
    
    # [파트 1] 국내 뉴스 수집
    message += "🇰🇷 *[국내 주요 경제 및 일간지]*\n"
    dom_count = 0
    for kw in KEYWORDS:
        articles = fetch_articles_by_sources(kw, DOMESTIC_SOURCES)
        if articles:
            # 키워드당 가장 최신 기사 1개만 채택
            article = articles[0]
            if article['link'] not in seen_links:
                seen_links.add(article['link'])
                dom_count += 1
                message += f"• *[{kw}]* [{article['title']}]({article['link']})\n"
                message += f"  📝 _{article['summary']}_\n"
                message += f"  └ 출처: {article['source']}\n\n"
                
    if dom_count == 0:
        message += "• 수집된 국내 기사가 없습니다.\n\n"
    
    # [파트 2] 해외 외신 수집
    message += "🌐 *[해외 외신 및 전문 매체]*\n"
    over_count = 0
    for kw in KEYWORDS:
        articles = fetch_articles_by_sources(kw, OVERSEAS_SOURCES)
        if articles:
            article = articles[0]
            if article['link'] not in seen_links:
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
