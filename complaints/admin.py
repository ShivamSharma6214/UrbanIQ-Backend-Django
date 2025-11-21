from django.contrib import admin
from .models import Complaint

# Register your models here.
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'complaint_type', 'is_active', 'created_at', 'updated_at')
    list_filter = ('complaint_type', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'user__username', 'user__email')


admin.site.register(Complaint, ComplaintAdmin)