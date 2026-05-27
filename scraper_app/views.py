import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from google_play_scraper import search
import requests
from bs4 import BeautifulSoup


def search_apps(request):
    results = []
    if request.method == "POST":
        keyword = request.POST.get('keyword')
        # 50 hits fetch karein taaki filter ke baad ache results milein
        apps = search(keyword, lang="en", country="in", n_hits=50)

        for app in apps:
            # Installs ko number mein convert karna
            installs_str = app.get('installs', '0').replace(',', '').replace('+', '')
            try:
                installs_count = int(installs_str)
            except:
                installs_count = 0

            # Filter: 500 se 5000 ke beech
            if 500 <= installs_count <= 5000:
                url = f"https://play.google.com/store/apps/details?id={app['appId']}"

                email, website, phone = "N/A", "N/A", "N/A"

                try:
                    response = requests.get(url, timeout=5)
                    soup = BeautifulSoup(response.content, 'html.parser')

                    email_tag = soup.find('a', href=lambda x: x and x.startswith('mailto:'))
                    if email_tag: email = email_tag.text

                    web_tag = soup.find('a', href=lambda
                        x: x and 'http' in x and 'play.google' not in x and 'mailto' not in x)
                    if web_tag: website = web_tag['href']

                    phone_tag = soup.find('a', href=lambda x: x and x.startswith('tel:'))
                    if phone_tag: phone = phone_tag.text
                except:
                    pass

                results.append({
                    'title': app.get('title', 'N/A'),
                    'installs': app.get('installs', 'N/A'),
                    'score': app.get('score', 0),
                    'email': email,
                    'website': website,
                    'phone': phone
                })

        request.session['search_data'] = results
    return render(request, 'index.html', {'results': results})


def download_excel(request):
    data = request.session.get('search_data')
    if not data: return HttpResponse("No data found.")
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="filtered_apps.xlsx"'
    df.to_excel(response, index=False)
    return response