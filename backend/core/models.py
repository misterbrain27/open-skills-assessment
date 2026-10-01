from django.db import models


class TimeStampedModel(models.Model):
    """Ajoute created_at et updated_at à tous les modèles du projet.

    Pas d'ordering : il serait hérité par tous les modèles et trierait chaque requête.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
