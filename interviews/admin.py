from django.contrib import admin
from .models import Question, Interview, Interview_Type, Type_Choice, Answer, Repository

admin.site.register(Question)
admin.site.register(Interview)
admin.site.register(Interview_Type)
admin.site.register(Type_Choice)
admin.site.register(Answer)
admin.site.register(Repository)
