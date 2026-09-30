# apps/customers/utils.py — NEW FILE
#
# pip install user-agents  (pulls in ua-parser automatically)

import logging
import requests
from user_agents import parse as parse_user_agent_string

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Real client IP — checks X-Forwarded-For first, since anything behind
    ngrok, nginx, or a load balancer puts the real IP there and
    request.META['REMOTE_ADDR'] would otherwise just be the proxy's own
    address (or ngrok's internal address).
    """
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        # X-Forwarded-For can be a comma-separated chain of proxies;
        # the first entry is the original client
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def parse_user_agent(ua_string):
    """Returns {'device': ..., 'os': ..., 'browser': ...} from a raw
    User-Agent header string."""
    if not ua_string:
        return {'device': 'অজানা ডিভাইস', 'os': 'অজানা', 'browser': 'অজানা'}

    ua = parse_user_agent_string(ua_string)

    if ua.is_mobile:
        device = 'মোবাইল'
    elif ua.is_tablet:
        device = 'ট্যাবলেট'
    elif ua.is_pc:
        device = 'কম্পিউটার'
    else:
        device = 'অজানা ডিভাইস'

    os_str = f"{ua.os.family} {ua.os.version_string}".strip()
    browser_str = f"{ua.browser.family} {ua.browser.version_string}".strip()

    return {
        'device': device,
        'os': os_str or 'অজানা',
        'browser': browser_str or 'অজানা',
    }


def get_location_from_ip(ip_address):
    """
    Best-effort city/country lookup via ip-api.com's free tier (no key
    needed, ~45 requests/min limit — fine for per-login lookups).

    Always returns a dict, even on failure — callers should never need
    a try/except of their own. Private/local IPs (127.0.0.1, 192.168.x.x,
    ngrok's internal ranges, etc.) can't be geolocated and will come back
    as "Unknown" — that's expected in local development.
    """
    fallback = {'city': '', 'country': ''}

    if not ip_address or ip_address in ('127.0.0.1', 'localhost', '::1'):
        return fallback

    try:
        resp = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=3)
        data = resp.json()
        if data.get('status') == 'success':
            return {
                'city': data.get('city', ''),
                'country': data.get('country', ''),
            }
    except Exception as e:
        logger.warning(f"IP geolocation lookup failed for {ip_address}: {e}")

    return fallback