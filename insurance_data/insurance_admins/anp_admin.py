# insurance_data/admin.py
import pandas as pd
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path, resolve, reverse

from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db import transaction
from django.contrib.auth import get_user_model
from unfold.decorators import display, action
from insurance_data.models import ANP, ANPImport, CaseCount, TopQuartileStatus
from insurance_data.forms import ANPImportForm, CaseCountImportForm
import pandas as pd
import os


class ANPAdminMixin(admin.ModelAdmin):
    list_display = [
        'agent_name',
        'month_year_badge',
        'total_anp_formatted',
        'life_rp_formatted',
        'life_sp_formatted',
        'health_shield_formatted',
        'pa_formatted',
        'cs_formatted',
    ]

    list_filter = [
        'year',
        'month',
    ]

    search_fields = ['agent_name']
    list_per_page = 50

    def get_form(self, rquest, object, **fields):
        return ANPImportForm

    def get_queryset(self, request):
        return super().get_queryset(request).filter(year=2025)

    @display(description='Period', ordering='year')
    def month_year_badge(self, obj):
        return format_html(
            '<span style="background: linear-gradient(135deg, #667eea, #764ba2); '
            'color: white; padding: 6px 12px; border-radius: 16px; '
            'font-size: 12px; font-weight: 600;">{}</span>',
            obj.month_year_display
        )

    @display(description='Total ANP', ordering='total_anp')
    def total_anp_formatted(self, obj):
        if obj.total_anp > 0:
            return format_html(
                f'<strong style="color: #059669; font-size: 14px;'
                '">₹ %.2f </strong>' % (obj.total_anp),
            )
        return format_html('<span style="color: #dc2626;">₹0.00</span>')

    @display(description='Life RP', ordering='life_rp')
    def life_rp_formatted(self, obj):
        return format_html('₹%.2f' % (obj.total_anp, ), obj.life_rp)\
            if obj.life_rp else '₹0.00'

    @display(description='Life SP', ordering='life_sp')
    def life_sp_formatted(self, obj):
        return format_html('₹%.2f' % (obj.life_sp,))\
            if obj.life_sp else '₹0.00'

    @display(description='Health Shield', ordering='health_shield')
    def health_shield_formatted(self, obj):
        return format_html('₹%.2f' % (obj.health_shield,))\
            if obj.health_shield else '₹0.00'

    @display(description='PA', ordering='pa')
    def pa_formatted(self, obj):
        return format_html('₹%.2f' % (obj.pa,))\
            if obj.pa else '₹0.00'

    @display(description='CS', ordering='cs')
    def cs_formatted(self, obj):
        return format_html('₹%.2f' % (obj.cs,))\
            if obj.cs else '₹0.00'
