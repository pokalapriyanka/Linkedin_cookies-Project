from django.urls import path
from .views import scrape_linkedin,scrape_results

urlpatterns = [
    path('scrape/', scrape_linkedin, name='scrape_linkedin'),
    path('results/', scrape_results, name='scrape_results'),
]
