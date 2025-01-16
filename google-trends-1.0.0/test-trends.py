from pytrends.request import TrendReq
import pandas as pd

# Google Trends 요청 객체 생성
pytrends = TrendReq(hl="ko-KR", tz=360)

# 키워드 및 설정
keywords = ["증권", "주식", "코스피", "ETF", "투자"]
category_id = 7  # 금융 카테고리
geo = "KR"  # 대한민국
timeframe = "today 12-m"  # 지난 12개월

# 1. Payload 생성
# - Google Trends 데이터를 요청할 키워드, 카테고리, 시간 등을 설정.
pytrends.build_payload(
    keywords,
    cat=category_id,
    timeframe=timeframe,
    geo=geo,
    gprop=""
)

# 2. 시간에 따른 관심도 데이터 가져오기
print("\n[시간에 따른 관심도]")
interest_over_time = pytrends.interest_over_time()
print(interest_over_time.head())

# 3. 지역별 관심도 데이터 가져오기
print("\n[지역별 관심도]")
interest_by_region = pytrends.interest_by_region(resolution="REGION")
print(interest_by_region.head())

# 4. 연관 검색어 데이터 가져오기 (오류 처리 포함)
print("\n[연관 검색어]")
try:
    related_queries = pytrends.related_queries()
    if related_queries:
        for kw, data in related_queries.items():
            print(f"\n{kw} - 상위 연관 검색어:")
            if data.get("top") is not None:
                print(data["top"].head())
            else:
                print("상위 연관 검색어 데이터 없음")
            
            print(f"{kw} - 상승 중인 연관 검색어:")
            if data.get("rising") is not None:
                print(data["rising"].head())
            else:
                print("상승 중인 연관 검색어 데이터 없음")
    else:
        print("연관 검색어 데이터 없음")
except IndexError:
    print("연관 검색어 데이터가 없습니다.")

# 5. 현재 인기 검색어 가져오기
print("\n[현재 인기 검색어]")
trending_searches = pytrends.trending_searches(pn="south_korea")
print(trending_searches.head())

# 6. 특정 연도의 인기 차트 가져오기
print("\n[2025 인기 차트]")
try:
    top_charts = pytrends.top_charts(2025, geo="KR")
    print(top_charts.head())
except Exception as e:
    print(f"인기 차트를 가져올 수 없습니다: {e}")

# 7. 추천 검색어 가져오기
print("\n[추천 검색어]")
try:
    suggestions = pytrends.suggestions("증권")
    print(pd.DataFrame(suggestions))
except Exception as e:
    print(f"추천 검색어를 가져올 수 없습니다: {e}")

# 8. 시간별 관심도 데이터 가져오기
print("\n[시간별 관심도 데이터]")
try:
    historical_interest = pytrends.get_historical_interest(
        keywords,
        year_start=2025,
        month_start=1,
        day_start=1,
        hour_start=0,
        year_end=2025,
        month_end=12,
        day_end=31,
        hour_end=23,
        geo=geo
    )
    print(historical_interest.head())
except Exception as e:
    print(f"시간별 관심도 데이터를 가져올 수 없습니다: {e}")
