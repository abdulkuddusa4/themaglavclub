# insurance_data/admin.py
import pandas as pd
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path

# @admin.register(AgentANPByProductYearly)
# class AgentAnpByProductYearlyAdmin(admin.ModelAdmin):
#     def get_form(self,request, obj, **fields):
#         print(obj)
#         print(fields)
#         return ExcelUploadForm

#     def save_model(self, request, obj, form, change):
#         # form is your MyCustomAdminForm
#         data = form.cleaned_data
#         # Manually create or update the model
#         print(data)
#         # obj.name = data['name']
#         # obj.email = data['email']
#         # obj.age = data.get('age')
#         # obj.save()

from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.db import transaction
from unfold.admin import ModelAdmin
from unfold.decorators import display, action
from .models import ANP, ANPImport, CaseCount
from .forms import ANPImportForm, CaseCountImportForm
import pandas as pd
import os


@admin.register(ANP)
class ANPAdmin(ModelAdmin):
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

    # fieldsets = (
    #     ('Agent Information', {
    #         'fields': ('agent_name',),
    #         'classes': ('wide',),
    #     }),
    #     ('ANP Data', {
    #         'fields': ('life_rp', 'life_sp', 'health_shield', 'pa', 'cs', 'total_anp'),
    #         'classes': ('wide',),
    #     }),
    #     ('Period', {
    #         'fields': ('month', 'year'),
    #         'classes': ('wide',),
    #     }),
    # )
    # def save_model(self, request, object, form, change):
    #     return redirect("http://127.0.0.1:3000/admin/insurance_data/anp/")
    #     return redirect(reverse(
    #         f"admin:{ANP._meta.app_label}_{ANP._meta.model_name}"
    #     ))

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


@admin.register(CaseCount)
class CaseCountAdmin(ModelAdmin):
    # form = CaseCountImportForm

    def get_form(self, request, object, **fields):
        return CaseCountImportForm
    list_display = [
        'agent_display',
        'year_badge',
        'ytd_case_formatted',
        'ytd_growth_formatted',
        'ytd_contribution_formatted',
        'top_quartile_mtd_badge',
        'top_quartile_ytd_badge',
        'current_month_value',
        'quarterly_summary',
    ]

    list_filter = [
        'year',
        'TOP_QUARTILE_MTD',
        'TOP_QUARTILE_YTD',
        ('agent__first_name', admin.AllValuesFieldListFilter),
        ('agent__last_name', admin.AllValuesFieldListFilter),
    ]

    search_fields = [
        'agent__first_name',
        'agent__last_name', 
        'agent__email',
        'agent__agent_code',
    ]

    list_per_page = 50
    ordering = ['-year', '-YTD_CASE']

    # fieldsets = (
    #     ('Agent & Year Information', {
    #         'fields': ('agent', 'year'),
    #         'classes': ('wide',),
    #     }),
    #     ('Top Quartile Status', {
    #         'fields': ('TOP_QUARTILE_MTD', 'TOP_QUARTILE_YTD'),
    #         'classes': ('wide',),
    #     }),
    #     ('Monthly Performance (Jan - Jun)', {
    #         'fields': ('JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN'),
    #         'classes': ('wide',),
    #     }),
    #     ('Monthly Performance (Jul - Dec)', {
    #         'fields': ('JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'),
    #         'classes': ('wide',),
    #     }),
    #     ('Year-to-Date Summary', {
    #         'fields': ('YTD_CASE', 'YTD_GROWTH', 'YTD_CONTRIBUTION_TO_UNIT'),
    #         'classes': ('wide',),
    #     }),
    # )
    
    readonly_fields = ['calculated_ytd', 'months_summary']
    def save_model(self, request, obj, form, change):
        # form is your MyCustomAdminForm
        raise Exception()
        data = form.cleaned_data
        print("DEBUG XL FILE")
        print(data.get('excel_file'))
        # Manually create or update the model
        print(data)
        # obj.name = data['name']
        # obj.email = data['email']
        # obj.age = data.get('age')
        # obj.save()

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('agent')
    
    @display(description='Agent', ordering='agent__last_name')
    def agent_display(self, obj):
        agent_name = f"{obj.agent.first_name} {obj.agent.last_name}".strip()
        if not agent_name:
            agent_name = obj.agent.username
        
        agent_code = getattr(obj.agent, 'agent_code', None)
        if agent_code:
            return format_html(
                '<div style="line-height: 1.4;">'
                '<strong style="color: #1f2937; font-size: 13px;">{}</strong><br>'
                '<span style="color: #6b7280; font-size: 11px;">Code: {}</span>'
                '</div>',
                agent_name, agent_code
            )
        return format_html('<strong style="color: #1f2937;">{}</strong>', agent_name)
    
    @display(description='Year', ordering='year')
    def year_badge(self, obj):
        return format_html(
            '<span style="background: linear-gradient(135deg, #667eea, #764ba2); '
            'color: white; padding: 6px 12px; border-radius: 16px; '
            'font-size: 12px; font-weight: 600;">{}</span>',
            obj.year
        )
    
    @display(description='YTD Cases', ordering='YTD_CASE')
    def ytd_case_formatted(self, obj):
        if obj.YTD_CASE > 0:
            return format_html(
                '<strong style="color: #059669; font-size: 14px;">{:,.2f}</strong>',
                obj.YTD_CASE
            )
        return format_html('<span style="color: #dc2626;">0.00</span>')
    
    @display(description='YTD Growth', ordering='YTD_GROWTH')
    def ytd_growth_formatted(self, obj):
        growth_percent = obj.YTD_GROWTH * 100  # Convert to percentage
        
        if obj.YTD_GROWTH > 0:
            return format_html(
                '<span style="color: #059669; font-weight: 600;">▲ {:.2f}%</span>',
                growth_percent
            )
        elif obj.YTD_GROWTH < 0:
            return format_html(
                '<span style="color: #dc2626; font-weight: 600;">▼ {:.2f}%</span>',
                abs(growth_percent)
            )
        else:
            return format_html('<span style="color: #6b7280;">0.00%</span>')
    
    @display(description='Unit Contribution', ordering='YTD_CONTRIBUTION_TO_UNIT')
    def ytd_contribution_formatted(self, obj):
        contribution_percent = obj.YTD_CONTRIBUTION_TO_UNIT * 100
        
        if contribution_percent >= 10:
            color = '#059669'  # Green for high contribution
        elif contribution_percent >= 5:
            color = '#d97706'  # Orange for medium contribution
        else:
            color = '#6b7280'  # Gray for low contribution
            
        return format_html(
            '<span style="color: {}; font-weight: 600;">{:.2f}%</span>',
            color, contribution_percent
        )
    
    @display(description='MTD Status')
    def top_quartile_mtd_badge(self, obj):
        colors = {
            TopQuartileStatus.YES: ('#10b981', '✓ Top Quartile'),
            TopQuartileStatus.NO: ('#ef4444', '✗ Below'),
            TopQuartileStatus.NA: ('#6b7280', 'N/A'),
        }
        color, text = colors.get(obj.TOP_QUARTILE_MTD, ('#6b7280', 'Unknown'))
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color, text
        )
    
    @display(description='YTD Status')
    def top_quartile_ytd_badge(self, obj):
        colors = {
            TopQuartileStatus.YES: ('#10b981', '✓ Top Quartile'),
            TopQuartileStatus.NO: ('#ef4444', '✗ Below'),
            TopQuartileStatus.NA: ('#6b7280', 'N/A'),
        }
        color, text = colors.get(obj.TOP_QUARTILE_YTD, ('#6b7280', 'Unknown'))
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color, text
        )
    
    @display(description='Current Month')
    def current_month_value(self, obj):
        """Show the latest month with data"""
        import datetime
        current_month = datetime.datetime.now().month
        
        month_values = [
            obj.JAN, obj.FEB, obj.MAR, obj.APR, obj.MAY, obj.JUN,
            obj.JUL, obj.AUG, obj.SEP, obj.OCT, obj.NOV, obj.DEC
        ]
        
        month_names = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ]
        
        # Find the last non-zero month or current month
        last_month_index = current_month - 1 if current_month <= 12 else 11
        for i in range(last_month_index, -1, -1):
            if month_values[i] > 0:
                return format_html(
                    '<span style="color: #1f2937; font-weight: 600;">{}: {:.2f}</span>',
                    month_names[i], month_values[i]
                )
        
        return format_html('<span style="color: #6b7280;">No data</span>')
    
    @display(description='Quarterly View')
    def quarterly_summary(self, obj):
        """Show quarterly breakdown"""
        q1 = obj.JAN + obj.FEB + obj.MAR
        q2 = obj.APR + obj.MAY + obj.JUN
        q3 = obj.JUL + obj.AUG + obj.SEP
        q4 = obj.OCT + obj.NOV + obj.DEC
        
        quarters = [
            ('Q1', q1, '#3b82f6'),
            ('Q2', q2, '#10b981'), 
            ('Q3', q3, '#f59e0b'),
            ('Q4', q4, '#ef4444'),
        ]
        
        html = '<div style="display: flex; gap: 4px;">'
        for quarter, value, color in quarters:
            if value > 0:
                html += f'<span style="background-color: {color}; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: 600;">{quarter}: {value:.0f}</span>'
            else:
                html += f'<span style="background-color: #e5e7eb; color: #6b7280; padding: 2px 6px; border-radius: 8px; font-size: 10px;">{quarter}: 0</span>'
        html += '</div>'
        
        return format_html(html)
    
    def calculated_ytd(self, obj):
        """Show calculated YTD from sum of months"""
        calculated = obj.sum_of_months
        stored = obj.YTD_CASE
        
        if abs(calculated - stored) > Decimal('0.01'):
            return format_html(
                '<div style="color: #dc2626;">'
                'Calculated: {:.2f}<br>'
                'Stored: {:.2f}<br>'
                '<strong>⚠️ Mismatch!</strong>'
                '</div>',
                calculated, stored
            )
        else:
            return format_html(
                '<span style="color: #059669;">✓ {:.2f}</span>',
                calculated
            )
    calculated_ytd.short_description = 'Calculated YTD'
    
    def months_summary(self, obj):
        """Show all months in a compact format"""
        months = [
            ('Jan', obj.JAN), ('Feb', obj.FEB), ('Mar', obj.MAR),
            ('Apr', obj.APR), ('May', obj.MAY), ('Jun', obj.JUN),
            ('Jul', obj.JUL), ('Aug', obj.AUG), ('Sep', obj.SEP),
            ('Oct', obj.OCT), ('Nov', obj.NOV), ('Dec', obj.DEC),
        ]

        html = '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 11px;">'
        for month, value in months:
            color = '#059669' if value > 0 else '#6b7280'
            html += f'<span style="color: {color};"><strong>{month}:</strong> {value:.2f}</span>'
        html += '</div>'

        return format_html(html)
    months_summary.short_description = 'Monthly Breakdown'

    # Custom actions
    actions = ['recalculate_ytd', 'mark_top_quartile_mtd', 'mark_top_quartile_ytd']

    @admin.action(description='Recalculate YTD from monthly data')
    def recalculate_ytd(self, request, queryset):
        updated = 0
        for obj in queryset:
            calculated_ytd = obj.sum_of_months
            if obj.YTD_CASE != calculated_ytd:
                obj.YTD_CASE = calculated_ytd
                obj.save(update_fields=['YTD_CASE'])
                updated += 1

        self.message_user(request, f'Recalculated YTD for {updated} records.')

    @admin.action(description='Mark as Top Quartile MTD')
    def mark_top_quartile_mtd(self, request, queryset):
        updated = queryset.update(TOP_QUARTILE_MTD=TopQuartileStatus.YES)
        self.message_user(request, f'Marked {updated} records as Top Quartile MTD.')

    @admin.action(description='Mark as Top Quartile YTD') 
    def mark_top_quartile_ytd(self, request, queryset):
        updated = queryset.update(TOP_QUARTILE_YTD=TopQuartileStatus.YES)
        self.message_user(request, f'Marked {updated} records as Top Quartile YTD.')
