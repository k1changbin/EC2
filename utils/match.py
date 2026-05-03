import math
from utils.config import MAX_VALUES

def match_player(user_stats, players):
    """
    유저의 설문 점수와 선수 데이터를 비교하여 유사도가 높은 순으로 정렬
    1순위: 코사인 유사도 (플레이 스타일/모양 일치도)
    2순위: 절대 점수 차이 (모양이 똑같을 경우 실력대 비슷한 선수 우선)
    """
    results = []
    
    # 1. 항목 순서 고정
    stats_keys = list(MAX_VALUES.keys())
    
    # 2. 유저의 점수 벡터 생성
    user_vec = [user_stats.get(k, 0) for k in stats_keys]
    
    for p in players:
        # 3. 선수의 점수 벡터 생성
        p_vec = [p.get(k, 0) for k in stats_keys]
        
        # 4. 코사인 유사도(Cosine Similarity) 계산
        dot_product = sum(u * v for u, v in zip(user_vec, p_vec))
        user_mag = math.sqrt(sum(u ** 2 for u in user_vec))
        p_mag = math.sqrt(sum(v ** 2 for v in p_vec))
        
        if user_mag == 0 or p_mag == 0:
            similarity = 0
        else:
            raw_sim = dot_product / (user_mag * p_mag)
            raw_sim = min(1.0, raw_sim)  # 부동 소수점 오차 방어
            similarity = round(raw_sim * 100, 1) # 순수 모양 일치도 계산
            
        # 5. 절대 점수 차이(diff) 계산 
        # (순위 결정 시 타이브레이커용으로만 사용하고, %를 깎지는 않음)
        diff_sum = sum(abs(u - v) for u, v in zip(user_vec, p_vec))
        
        final_sim = similarity 
            
        # 선수 데이터 복사본에 결과값 저장
        p_copy = p.copy()
        p_copy['similarity'] = final_sim  
        p_copy['diff'] = diff_sum
        results.append(p_copy)
    
    # 6. 다중 조건 정렬
    # -x['similarity']: 싱크로율(모양)이 최우선 (내림차순)
    # x['diff']: 만약 모양 일치도가 소수점까지 같다면, 그나마 실력이 비슷한 선수가 위로 (오름차순)
    return sorted(results, key=lambda x: (-x['similarity'], x['diff']))