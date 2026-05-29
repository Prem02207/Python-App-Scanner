import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from google_play_scraper import search
import requests
from bs4 import BeautifulSoup


def search_apps(request):
    results = []
    # User dwara daala gaya keyword capture karein
    keyword = request.POST.get('keyword', '')

    if request.method == "POST":
        try:
            # Google Play Store se search results fetch karein
            apps = search(keyword, lang="en", country="in", n_hits=50)

            for app in apps:
                # Installs count ko integer mein badlein
                installs_str = app.get('installs', '0').replace(',', '').replace('+', '')
                installs_count = int(installs_str) if installs_str.isdigit() else 0

                # 500 se 5000 install filter
                if 500 <= installs_count <= 5000:
                    url = f"https://play.google.com/store/apps/details?id={app['appId']}"
                    email, website, phone = "N/A", "N/A", "N/A"

                    try:
                        resp = requests.get(url, timeout=5)
                        soup = BeautifulSoup(resp.content, 'html.parser')

                        # Email Extraction
                        email_tag = soup.find('a', href=lambda x: x and x.startswith('mailto:'))
                        if email_tag:
                            email = email_tag['href'].replace('mailto:', '').split('?')[0]

                        # Precise Website Extraction (aria-label)
                        web_tag = soup.find('a', {'aria-label': lambda x: x and 'website' in x.lower()})
                        if web_tag and web_tag.has_attr('href'):
                            website = web_tag['href'].replace('https://', '').replace('http://', '').split('/')[0]

                        # Phone Extraction
                        phone_tag = soup.find('a', href=lambda x: x and x.startswith('tel:'))
                        if phone_tag:
                            phone = phone_tag.text
                    except:
                        pass  # Agar site load na ho toh ignore karein

                    results.append({
                        'title': app.get('title'),
                        'appId': app['appId'],
                        'installs': app.get('installs'),
                        'score': app.get('score', 0),
                        'email': email,
                        'website': website,
                        'phone': phone
                    })

            # Data aur Keyword ko Session mein save karein taaki Download feature use kar sake
            request.session['search_data'] = results
            request.session['search_keyword'] = keyword

        except Exception as e:
            print(f"Error: {e}")

    return render(request, 'index.html', {'results': results})


def download_excel(request):
    # Session se data aur keyword nikalen
    data = request.session.get('search_data')
    keyword = request.session.get('search_keyword', 'apps_data')

    if not data:
        return HttpResponse("No data available to download.")

    # Pandas DataFrame banayein
    df = pd.DataFrame(data)

    # Dynamic Filename: Keyword_apps.xlsx
    filename = f"{keyword}_apps.xlsx"

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Excel mein data export karein
    df.to_excel(response, index=False)
    return response