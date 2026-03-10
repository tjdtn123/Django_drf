def get_client_ip(request) -> str:
    """X-Forwarded-For 헤더 우선, 없으면 REMOTE_ADDR"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def get_device_type(user_agent: str) -> str:
    """User-Agent로 디바이스 타입 판별"""
    ua = user_agent.lower()
    if any(kw in ua for kw in ('ipad', 'tablet', 'android' + ' ')):
        return 'tablet'
    if any(kw in ua for kw in ('iphone', 'android', 'mobile', 'phone')):
        return 'mobile'
    return 'pc'
