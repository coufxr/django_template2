from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.account import views

app_name = "account"

router = SimpleRouter(trailing_slash=False)

urlpatterns = router.urls + [
    path("/captcha", views.CaptchaView.as_view()),
    path("/login", views.AccountTokenObtainPairView.as_view()),
    path("/logout", views.AccountLogoutView.as_view()),
    path("/info", views.AccountInfoView.as_view()),
    path("/phone", views.AccountPhoneView.as_view()),
]
