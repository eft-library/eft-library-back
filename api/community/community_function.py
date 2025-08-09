import re

class CommunityFunction:

    @staticmethod
    def extract_thumbnail_img(html):
        # 정규 표현식을 사용하여 첫 번째 <img> 태그의 src 값 찾아서 썸네일 반환
        match = re.search(r'<img[^>]+src="([^"]+)"', html)
        if match:
            return match.group(1)
        return None