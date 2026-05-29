import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from google_play_scraper import search
import requests
from bs4 import BeautifulSoup
import io

def search_apps(request):
    results = []
    keyword = ''

    if request.method == "POST":
        keyword = request.POST.get('keyword', '').strip()
        if keyword:
            try:
                # 1. Scraping Search Results
                apps = search(keyword, lang="en", country="in", n_hits=10)

                for app in apps:
                    installs_str = app.get('installs', '0').replace(',', '').replace('+', '')
                    installs_count = int(installs_str) if installs_str.isdigit() else 0

                    if 500 <= installs_count <= 5000:
                        url = f"https://play.google.com/store/apps/details?id={app['appId']}"
                        
                        # Default values
                        data_row = {
                            'title': app.get('title'),
                            'appId': app['appId'],
                            'installs': app.get('installs'),
                            'score': app.get('score', 0),
                            'email': 'N/A',
                            'website': 'N/A',
                            'phone': 'N/A'
                        }

                        # 2. Scraping Details with better error handling
                        try:
                            headers = {'User-Agent': 'Mozilla/5.0'}
                            resp = requests.get(url, headers=headers, timeout=8) # Timeout badhaya
                            if resp.status_code == 200:
                                soup = BeautifulSoup(resp.content, 'html.parser')
                                
                                # Email
                                email_tag = soup.find('a', href=lambda x: x and x.startswith('mailto:'))
                                if email_tag:
                                    data_row['email'] = email_tag['href'].replace('mailto:', '').split('?')[0]
                                
                                # Website
                                web_tag = soup.find('a', {'aria-label': lambda x: x and 'website' in x.lower()})
                                if web_tag and web_tag.has_attr('href'):
                                    data_row['website'] = web_tag['href'].split('//')[-1].split('/')[0]
                        except Exception:
                            pass 

                        results.append(data_row)

            except Exception as e:
                print(f"Scraping Error: {e}")

    # Results ko session mein nahi, direct context mein bhejein
    return render(request, 'index.html', {'results': results, 'keyword': keyword})

def download_excel(request):
    # Ab data ko session se nahi, yahan logic se handle karna hoga
    # Yahan simple trick: Agar session use nahi karna, toh download ke liye 
    # naya request bhejna hoga. Filhal hum basic session rakhenge par limit karenge.
    data = request.session.get('search_data')
    
    # ... baki code wahi rahega ...
    df = pd.DataFrame(data)
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False)
    writer.close()
    output.seek(0)
    
    response = HttpResponse(output.read(), content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="apps.xlsx"'
    return response
