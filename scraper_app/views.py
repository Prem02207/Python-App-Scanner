import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from google_play_scraper import search
import requests
from bs4 import BeautifulSoup

def search_apps(request):
    results = []
    keyword = '' # Default khali rakhein

    if request.method == "POST":
        keyword = request.POST.get('keyword', '').strip() # Strip extra spaces
        if keyword:
            try:
                # Google Play Store se search results fetch karein
                apps = search(keyword, lang="en", country="in", n_hits=5) # n_hits kam rakhein taaki speed achhi rahe

                for app in apps:
                    # Installs count ko integer mein badlein
                    installs_str = app.get('installs', '0').replace(',', '').replace('+', '')
                    installs_count = int(installs_str) if installs_str.isdigit() else 0

                    # 500 se 5000 install filter
                    if 500 <= installs_count <= 5000:
                        url = f"https://play.google.com/store/apps/details?id={app['appId']}"
                        email, website, phone = "N/A", "N/A", "N/A"

                        try:
                            # Scraping ka kaam
                            headers = {'User-Agent': 'Mozilla/5.0'}
                            resp = requests.get(url, headers=headers, timeout=5)
                            soup = BeautifulSoup(resp.content, 'html.parser')

                            # Email Extraction
                            email_tag = soup.find('a', href=lambda x: x and x.startswith('mailto:'))
                            if email_tag:
                                email = email_tag['href'].replace('mailto:', '').split('?')[0]

                            # Precise Website Extraction
                            web_tag = soup.find('a', {'aria-label': lambda x: x and 'website' in x.lower()})
                            if web_tag and web_tag.has_attr('href'):
                                website = web_tag['href'].replace('https://', '').replace('http://', '').split('/')[0]

                            # Phone Extraction
                            phone_tag = soup.find('a', href=lambda x: x and x.startswith('tel:'))
                            if phone_tag:
                                phone = phone_tag.text
                        except:
                            pass

                        results.append({
                            'title': app.get('title'),
                            'appId': app['appId'],
                            'installs': app.get('installs'),
                            'score': app.get('score', 0),
                            'email': email,
                            'website': website,
                            'phone': phone
                        })

                # Session mein save karein
                request.session['search_data'] = results
                request.session['search_keyword'] = keyword

            except Exception as e:
                print(f"Error: {e}")

    # Results aur keyword dono template ko bhej rahe hain
    return render(request, 'index.html', {'results': results, 'keyword': keyword})

def download_excel(request):
    data = request.session.get('search_data')
    keyword = request.session.get('search_keyword', 'apps_data')

    if not data:
        return HttpResponse("No data available to download.")

    df = pd.DataFrame(data)
    filename = f"{keyword}_apps.xlsx"
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    df.to_excel(response, index=False)
    return response
