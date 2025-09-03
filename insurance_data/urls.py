from django.urls import path
from .views import (
    leaderboard_view
)

urlpatterns = [
    path("leaderboard/", leaderboard_view),
]