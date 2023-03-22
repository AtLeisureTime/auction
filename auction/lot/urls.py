from django.urls import path
from . import views

app_name = 'lot'

urlpatterns = [
    path('', views.LotListView.as_view(), name='lotList'),
    path('<int:lotId>', views.LotDetailView.as_view(), name='lotStakes'),
    path('<slug:auctnState>', views.LotListView.as_view(), name='lotListByAuctnType'),
]
