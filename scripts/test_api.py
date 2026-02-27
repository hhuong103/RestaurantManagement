import requests
url='http://127.0.0.1:5000/api/get_order_by_qr'
payload={'qr_code':'ORDER#78#RESTAURANT'}
try:
    r=requests.post(url,json=payload,timeout=10)
    print('Status:', r.status_code)
    try:
        print('JSON:', r.json())
    except Exception as e:
        print('Response text:', r.text)
except Exception as e:
    print('Request error:', e)
