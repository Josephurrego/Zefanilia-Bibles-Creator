import requests as rq
def getResponse(url:str):
    res = rq.get(url,headers={'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'})
    if res.status_code != 200:
        print(url)
    return res

def decodeHtml(text:str):
    return text.encode('utf-8').decode('unicode_escape')