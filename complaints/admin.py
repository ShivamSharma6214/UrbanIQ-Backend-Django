from django.contrib import admin
from django.utils.html import format_html
from .models import Complaint, ComplaintImage, ResolutionProofImage

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


class ResolutionProofInline(admin.TabularInline):
    model = ResolutionProofImage
    extra = 0
    readonly_fields = ('image_preview', 'created_at', 'updated_at')
    fields = ('image_preview', 'image', 'created_at', 'updated_at')
    verbose_name = "Resolution Proof Image"
    verbose_name_plural = "Resolution Proof Images"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" width="150" style="max-height:200px;" /></a>',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'complaint_type', 'status', 'is_active', 'created_at', 'updated_at')
    list_filter = ('complaint_type', 'status', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'location', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'image_gallery', 'resolution_proof_gallery')
    fieldsets = (
        ('Complaint Info', {
            'fields': ('user', 'title', 'description', 'location', 'complaint_type', 'status', 'is_active')
        }),
        ('Media', {
            'fields': ('image_gallery', 'resolution_proof_gallery', 'video')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ComplaintImageInline, ResolutionProofInline]
    
    def image_gallery(self, obj):
        if obj.images.exists():
            html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
            for img in obj.images.all():
                html += f'<img src="{img.image.url}" width="120" height="auto" style="max-height: 150px; border-radius: 5px;" />'
            html += '</div>'
            return format_html(html)
        return "No images uploaded"
    image_gallery.short_description = 'Image Gallery'

    def resolution_proof_gallery(self, obj):
        if obj.resolution_proofs.exists():
            html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
            for img in obj.resolution_proofs.all():
                html += f'<a href="{img.image.url}" target="_blank"><img src="{img.image.url}" width="120" style="max-height:150px; border-radius:5px;" /></a>'
            html += '</div>'
            return format_html(html)
        return "No resolution proof images"
    resolution_proof_gallery.short_description = 'Resolution Proofs'


admin.site.register(Complaint, ComplaintAdmin)
admin.site.register(ComplaintImage)
admin.site.register(ResolutionProofImage)