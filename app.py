from flask import Flask, request, Response
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

def rewrite_url(original_url, tag_attr_value):
    """相対パスを絶対パスに変換し、プロキシ経由のURLに書き換える関数"""
    absolute_url = urljoin(original_url, tag_attr_value)
    # request.host_url を使って、Renderのドメインを動的に取得
    proxy_base_url = request.host_url
    return f"{proxy_base_url}?url={absolute_url}"

@app.route('/')
def proxy():
    # Renderのドメインをベースにする
    proxy_base_url = request.host_url
    
    url = request.args.get('url')

    if not url:
        return f"""
            <h1>My Simple Web Proxy on Render</h1>
            <form action="{proxy_base_url}" method="get">
                <input type="text" name="url" size="50" placeholder="https://example.com">
                <input type="submit" value="Go">
            </form>
        """, 200

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        resp = requests.get(url, headers=headers)
        
        content_type = resp.headers.get('Content-Type', '').lower()

        if 'text/html' not in content_type:
            excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
            headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
            return Response(resp.content, resp.status_code, headers)

        soup = BeautifulSoup(resp.content, 'html.parser')

        # href属性を持つ全てのタグ（a, linkなど）
        for tag in soup.find_all(href=True):
            # JavaScriptのリンクやアンカーは書き換えない
            if not tag['href'].startswith(('javascript:', '#')):
                tag['href'] = rewrite_url(url, tag['href'])
        
        # src属性を持つ全てのタグ（img, scriptなど）
        for tag in soup.find_all(src=True):
            tag['src'] = rewrite_url(url, tag['src'])
            
        # action属性を持つformタグ
        for tag in soup.find_all('form', action=True):
            tag['action'] = rewrite_url(url, tag['action'])

        return str(soup)

    except requests.exceptions.RequestException as e:
        return f"エラー: URLの取得に失敗しました: {e}", 500
