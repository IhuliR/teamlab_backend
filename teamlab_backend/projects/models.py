from django.db import models

from .constants import (
    SPECIALIZATION_NAME_MAX_LEN,
    FIELD_NAME_MAX_LEN
)


class Field(models.Model):
    name = models.CharField(
        max_length=FIELD_NAME_MAX_LEN,
        unique=True,
        verbose_name='Название'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Область'
        verbose_name_plural = 'Области'
    
    def __str__(self):
        return self.name


class Specialization(models.Model):
    name = models.CharField(
        max_length=SPECIALIZATION_NAME_MAX_LEN,
        unique=True,
        verbose_name='Название'
    )
    field = models.ForeignKey(
        Field,
        on_delete=models.CASCADE,
        related_name='specializations',
        verbose_name='Область'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Специализация'
        verbose_name_plural = 'Специализации'
    
    def __str__(self):
        return self.name
