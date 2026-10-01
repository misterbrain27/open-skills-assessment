import pytest
from django.db import OperationalError
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


# Pas de marqueur django_db : pytest-django bloque alors tout accès à la base.
# Si la liveness touchait PostgreSQL, ce test échouerait.
def test_liveness_repond_sans_toucher_a_la_base(client):
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_readiness_repond_ok_quand_la_base_est_joignable(client):
    response = client.get(reverse("ready"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_renvoie_503_generique_quand_la_base_est_indisponible(
    client, monkeypatch, caplog
):
    detail = 'connection to server at "db-interne" failed'

    def panne():
        raise OperationalError(detail)

    monkeypatch.setattr("core.views.connection.ensure_connection", panne)

    response = client.get(reverse("ready"))

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert detail not in response.content.decode()
    # Le détail n'est pas perdu : il est dans les logs, avec la trace.
    assert detail in caplog.text
