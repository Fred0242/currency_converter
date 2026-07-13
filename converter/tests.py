import json
from django.test import TestCase, Client
from django.urls import reverse
from .services import get_exchange_rate, SUPPORTED_CURRENCIES
from .models import ConversionHistory
from django.contrib.auth.models import User


class CurrencyServicesTest(TestCase):
    """Tests du service de conversion."""

    def test_supported_currencies_not_empty(self):
        """Vérifie que la liste des devises n'est pas vide."""
        self.assertGreater(len(SUPPORTED_CURRENCIES), 0)

    def test_supported_currencies_have_required_keys(self):
        """Vérifie que chaque devise a les bonnes clés."""
        for currency in SUPPORTED_CURRENCIES:
            self.assertIn('code', currency)
            self.assertIn('country', currency)
            self.assertIn('name', currency)

    def test_xaf_in_supported_currencies(self):
        """Vérifie que le XAF est bien dans la liste."""
        codes = [c['code'] for c in SUPPORTED_CURRENCIES]
        self.assertIn('XAF', codes)


class ConverterViewTest(TestCase):
    """Tests des vues du convertisseur."""

    def setUp(self):
        """Initialise le client de test."""
        self.client = Client()

    def test_home_page_accessible(self):
        """La page d'accueil est accessible sans login."""
        response = self.client.get(reverse('converter-home'))
        self.assertEqual(response.status_code, 200)

    def test_home_page_contains_form(self):
        """La page contient bien un formulaire."""
        response = self.client.get(reverse('converter-home'))
        self.assertContains(response, '<form')

    def test_conversion_post_without_login(self):
        """Une conversion sans login fonctionne mais ne sauvegarde pas."""
        response = self.client.post(reverse('converter-home'), {
            'from_currency': 'EUR',
            'to_currency': 'USD',
            'amount': '100',
        })
        self.assertEqual(response.status_code, 200)
        # Pas d'historique sauvegardé sans login
        self.assertEqual(ConversionHistory.objects.count(), 0)

    def test_conversion_post_with_login_saves_history(self):
        """Une conversion avec login sauvegarde l'historique."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

        self.client.post(reverse('converter-home'), {
            'from_currency': 'EUR',
            'to_currency': 'USD',
            'amount': '100',
        })
        # L'historique doit contenir une entrée
        self.assertEqual(ConversionHistory.objects.filter(user=user).count(), 1)


class ConverterApiTest(TestCase):
    """Tests des endpoints HTTP JSON (API)."""

    def setUp(self):
        self.client = Client()

    def test_convert_api_without_login_does_not_save_history(self):
        """POST /api/convert/ calcule le résultat mais ne sauvegarde rien sans login."""
        response = self.client.post(
            reverse('convert-api'),
            data=json.dumps({'from_currency': 'EUR', 'to_currency': 'USD', 'amount': 100}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('converted', response.json())
        self.assertEqual(ConversionHistory.objects.count(), 0)

    def test_convert_api_with_login_saves_history(self):
        """POST /api/convert/ sauvegarde l'historique pour un utilisateur connecté."""
        user = User.objects.create_user(username='apiuser', password='testpass123')
        self.client.login(username='apiuser', password='testpass123')

        response = self.client.post(
            reverse('convert-api'),
            data=json.dumps({'from_currency': 'EUR', 'to_currency': 'USD', 'amount': 100}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ConversionHistory.objects.filter(user=user).count(), 1)

    def test_convert_api_rejects_unknown_currency(self):
        """POST /api/convert/ renvoie une erreur 400 pour une devise inconnue."""
        response = self.client.post(
            reverse('convert-api'),
            data=json.dumps({'from_currency': 'XXX', 'to_currency': 'USD', 'amount': 100}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_history_api_requires_login(self):
        """GET /api/history/ redirige si l'utilisateur n'est pas connecté."""
        response = self.client.get(reverse('history-api'))
        self.assertEqual(response.status_code, 302)

    def test_history_api_returns_user_history(self):
        """GET /api/history/ renvoie l'historique JSON de l'utilisateur connecté."""
        user = User.objects.create_user(username='historyuser', password='testpass123')
        ConversionHistory.objects.create(
            user=user, from_currency='EUR', to_currency='USD',
            amount=100, converted=108, rate=1.08,
        )
        self.client.login(username='historyuser', password='testpass123')

        response = self.client.get(reverse('history-api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['history']), 1)
        self.assertEqual(data['history'][0]['from_currency'], 'EUR')


class UsersViewTest(TestCase):
    """Tests des vues d'authentification."""

    def test_login_page_accessible(self):
        """La page de login est accessible."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_register_page_accessible(self):
        """La page d'inscription est accessible."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user(self):
        """L'inscription crée bien un utilisateur."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
        })
        self.assertEqual(User.objects.filter(username='newuser').count(), 1)