# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin


#class CustomUserAdmin(UserAdmin):
 #   actions = [
  #      'activate_users',
   # ]

def activate_users(self, request, queryset):
    cnt = queryset.filter(is_active=False).update(is_active=True)
    self.message_user(request, 'Activated {} users.'.format(cnt))
activate_users.short_description = 'Activate Users'  # type: ignore

#def get_actions(self, request):
 #   actions = super().get_actions(request)
  #  if not request.user.has_perm('auth.change_user'):
   #     del actions['activate_users']
    #return actions