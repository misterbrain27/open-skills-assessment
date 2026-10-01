from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings


def test_permission_par_defaut_exige_une_authentification():
    """Un endpoint sans permission_classes explicite doit être fermé, pas ouvert."""
    # api_settings importe réellement la classe : une faute de frappe dans le chemin
    # (ex. "isAuthenticated") fait échouer le test au lieu de passer inaperçue.
    assert api_settings.DEFAULT_PERMISSION_CLASSES == [IsAuthenticated]
