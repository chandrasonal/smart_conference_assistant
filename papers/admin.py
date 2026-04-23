from django.contrib import admin
from .models import Paper, Conference

@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'year')
    ordering     = ('-year', 'name')

@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display  = ('title', 'conference', 'created_at')
    list_filter   = ('conference',)
    search_fields = ('title', 'authors', 'abstract')
    ordering      = ('-created_at',)
