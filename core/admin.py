from django.contrib import admin

from core.models import Match, Room, Word

# Register your models here.
admin.site.register(Word)
admin.site.register(Match)
admin.site.register(Room)