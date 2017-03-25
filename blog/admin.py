from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.conf.urls import url
from django import forms
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from mptt.admin import MPTTModelAdmin

from .models import Post, Category, Media, Link, Comment, Commenter, WordpressPost
from .forms import BulkMediaForm

# Register your models here.

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = { 'slug': ['title'] }
    search_fields = ['title']
    list_display = ('title', 'get_full_url', 'get_wordpress_url', 'pub_date', 'admin_first_image')
    
    # add a link to the blog post on the admin list display to make it easier to preview the post
    def get_full_url(self, instance):
        return "<a href='%s'>%s</a>" % (instance.get_absolute_url(), instance.get_absolute_url())
    get_full_url.short_description = 'Link'
    get_full_url.allow_tags = True
    
    # show the first image on the admin list so we can make sure it gets set
    def admin_first_image(self, instance):
        if not instance.first_image:
            return u'None'
        return u'<img src="%s" height="150" />' % (instance.first_image.url)
        
    admin_first_image.short_description = 'First Image'
    admin_first_image.allow_tags = True
    
    # add a link to open the wordpress admin page
    def get_wordpress_url(self, instance):
        return "<a href='/admin/blog/wordpresspost/%d/change/'>/admin/blog/wordpresspost/%d/change/</a>" % (instance.id, instance.id) 
        
    get_wordpress_url.short_description = 'Wordpress'
    get_wordpress_url.allow_tags = True


@admin.register(WordpressPost)
class WordpressAdmin(PostAdmin):
    prepopulated_fields = {}
    fields = ('title', 'wordpress_body')
    list_display = ('title', 'get_full_url', 'pub_date', 'admin_first_image', )
    readonly_fields = ('title', 'wordpress_body')


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    prepopulated_fields = { 'slug': ['title'] }


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    search_fields = ['image_name']
    list_display = ('image_name', 'pub_date', 'admin_url', 'admin_thumbnail', 'admin_full', )
    bulk_upload_fields = ('full_image', )
    change_list_template = 'admin/blog/bulk_upload_list.html'

    def generate_data_for_file(self, request, field_name, field_file, index):
        if field_name == 'full_image':
            index_string = '{0:02d}'.format(index+1)
            return dict(image_name=index_string)
    
    def admin_url(self, instance):
        return "<a href='%s'>%s</a>" % (instance.get_blog_url(), instance.get_blog_url())
        
    admin_url.short_description = 'Image URL'
    admin_url.allow_tags = True
    
    # this stuff is to show a preview of the image in the admin list
    def admin_thumbnail(self, instance):
        if not instance.scale_image:
            return u'None'
        return u'<img src="%s" height="150" />' % (instance.scale_image.url)
        
    admin_thumbnail.short_description = 'Image'
    admin_thumbnail.allow_tags = True
    
    def admin_full(self, instance):
        return u'<img src="%s" height="150" />' % (instance.full_image.url)
        
    admin_full.short_description = 'Full Image'
    admin_full.allow_tags = True
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r'^bulk-upload/$',
                self.admin_site.admin_view(self.process_bulk_upload),
                name='bulk_upload',
            ),
        ]
        return custom_urls + urls
    
    def process_bulk_upload(self, request, *args, **kwargs):
        if request.method != 'POST':
            form = BulkMediaForm()
        else:
            form = BulkMediaForm(request.POST, request.FILES)
            if form.is_valid():
                counter = 0
                base_name = form.cleaned_data['name']
                for img in request.FILES.getlist('images'):
                    counter += 1
                    new_med = Media()
                    new_med.image_name = base_name + '-{0:02d}'.format(counter)
                    new_med.full_image = img
                    new_med.save()
                self.message_user(request, "Success")
            else:
                self.message_user(request, "Error occurred")
            url = reverse(
                'admin:blog_media_changelist',
                current_app=self.admin_site.name,
            )
            return HttpResponseRedirect(url)
        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        return TemplateResponse(
            request,
            'admin/blog/bulk_upload.html',
            context,
        )
    
    
@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    pass


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'pub_date', 'text', 'approved', 'notify', 'spam')
    list_filter = ['approved', 'spam']
    search_fields = ['author']
    actions = ['mark_approved', 'mark_not_approved', 'mark_spam', 'mark_not_spam']
    ordering = ['-pub_date']
    
    def mark_approved(self, request, queryset):
        for comment in queryset:
            comment.approve()
    
    mark_approved.short_description = "Approve the selected comments"
    
    def mark_not_approved(self, request, queryset):
        for comment in queryset:
            comment.unapprove()
    
    mark_not_approved.short_description = "Unapprove the selected comments"

    def mark_spam(self, request, queryset):
        for comment in queryset:
            comment.spam = True
            comment.save()
    
    mark_spam.short_description = "Mark the comments as spam"
    
    def mark_not_spam(self, request, queryset):
        for comment in queryset:
            comment.spam = False
            comment.save()
    
    mark_not_spam.short_description = "Mark the comments as safe"


@admin.register(Commenter)
class CommenterAdmin(admin.ModelAdmin):
    list_display = ('username', 'approved', 'spam')
    list_filter = ['approved', 'spam']
    search_fields = ['username']
    actions = ['mark_approved', 'mark_not_approved', 'mark_spam', 'mark_not_spam']
    
    def mark_approved(self, request, queryset):
        for commenter in queryset:
            commenter.approve()
    
    mark_approved.short_description = "Approve the selected users"
    
    def mark_not_approved(self, request, queryset):
        for commenter in queryset:
            commenter.unapprove()
    
    mark_not_approved.short_description = "Unapprove the selected users"
    
    def mark_spam(self, request, queryset):
        for commenter in queryset:
            commenter.mark_spam()
    
    mark_spam.short_description = "Mark the users as spammers"
    
    def mark_not_spam(self, request, queryset):
        for commenter in queryset:
            commenter.mark_safe()
    
    mark_not_spam.short_description = "Mark the users as safe"