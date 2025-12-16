from django.contrib import admin
from django.utils.html import format_html
from .models import Complaint, ComplaintImage

# Register your models here.

class ComplaintImageInline(admin.TabularInline):
    model = ComplaintImage
    extra = 0
    readonly_fields = ('image_preview', 'created_at', 'updated_at')
    fields = ('image_preview', 'image', 'created_at', 'updated_at')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="150" height="auto" style="max-height: 200px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'complaint_type', 'status', 'is_active', 'created_at', 'updated_at')
    list_filter = ('complaint_type', 'status', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'location', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'image_gallery')
    fieldsets = (
        ('Complaint Info', {
            'fields': ('user', 'title', 'description', 'location', 'complaint_type', 'status', 'is_active')
        }),
        ('Media', {
            'fields': ('image_gallery', 'video')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ComplaintImageInline]
    
    def image_gallery(self, obj):
        if obj.images.exists():
            html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
            for img in obj.images.all():
                html += f'<img src="{img.image.url}" width="120" height="auto" style="max-height: 150px; border-radius: 5px;" />'
            html += '</div>'
            return format_html(html)
        return "No images uploaded"
    image_gallery.short_description = 'Image Gallery'


admin.site.register(Complaint, ComplaintAdmin)
admin.site.register(ComplaintImage)