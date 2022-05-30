from django.contrib import admin

from core.models import Match, Room, SelectedWord, Word, WordsFile

# Register your models here.
admin.site.register(Word)
admin.site.register(Match)
admin.site.register(Room)
admin.site.register(SelectedWord)
admin.site.register(WordsFile)
