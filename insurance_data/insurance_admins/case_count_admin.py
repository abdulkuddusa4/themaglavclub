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

USER_MODEL = get_user_model()


class CaseCountAdminMixin(admin.ModelAdmin):
    # form = CaseCountImportForm

    list_display = [
        'agent_display',
        'top_quartile_mtd_badge',
        'top_quartile_ytd_badge',
        'JAN', 'FEB', 'MAR', 'APR',
        'MAY', 'JUN', 'JUL', 'AUG',
        'SEP', 'OCT', 'NOV', 'DEC',
        'year_badge',
        'ytd_case_formatted',
        'ytd_growth_formatted',
        'ytd_contribution_formatted',
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

    def has_change_permission(self, request, obj=None):
        print("&&&&")
        print("&&&&")
        print("&&&&")
        return False

    def get_form(self, request, object, **fields):
        return CaseCountImportForm

    def save_model(self, request, obj, form, change):

        data = form.cleaned_data
        print("DEBUG XL FILE")
        print(data.get('excel_file'))
        # Manually create or update the model
        print(data)

    def process_excel_file(self, file):
        errors = []
        if file:
            if file.size > 20 * 1024 * 1024:
                raise ValidationError('Excel file size must not exceed 20MB.')

            try:
                expected_schema = {
                    'Agent Name': 'string',
                    'Agent Code': 'string',
                    'JAN': 'float64',
                    'FEB': 'float64',
                    'MAR': 'float64',
                    'APR': 'float64',
                    'MAY': 'float64',
                    'JUN': 'float64',
                    'JUL': 'float64',
                    'AUG': 'float64',
                    'SEP': 'float64',
                    'OCT': 'float64',
                    'NOV': 'float64',
                    'DEC': 'float64',
                    'Top Quartile (MTD)': 'string',
                    'Top Quartile (YTD)': 'string',
                    'YTD_CASE': 'float64',
                    'YTD Growth': 'float64',
                    'YTD Contribution to Unit': 'float64'
                }

                valid_quartile_choices = ['TERMINATED', 'YES', 'NO', 'N/A']

                df = pd.read_excel(file)

                df.columns = df.columns.str.strip()

                missing_columns = set(expected_schema.keys()) - set(df.columns)

                if missing_columns:
                    errors.append(
                        f'Missing required columns: {", ".join(sorted(missing_columns))}. '
                        f'Found columns: {", ".join(df.columns.tolist())}'
                    )
                    return None, errors

                # Check for empty DataFrame
                if len(df) == 0:
                    errors.append('Excel file appears to be empty.')
                    return None, errors

                df = df[list(expected_schema.keys())]

                validation_errors = []

                try:
                    for column, dtype in expected_schema.items():
                        if dtype == 'string':
                            df[column] = df[column].astype('string').fillna('')

                            if column in ['Agent Name']:
                                empty_rows = df[df[column].str.strip() == ''].index
                                if len(empty_rows) > 0:
                                    row_numbers = [idx + 2 for idx in empty_rows[:5]]  # Show first 5
                                    errors.append(
                                        f'{column} is required but empty in rows: {row_numbers}'
                                        + ('...' if len(empty_rows) > 5 else '')
                                    )
                                    return None, errors

                            if column in ['Agent Code']:
                                # Check for duplicate agent codes within the DataFrame
                                duplicate_codes = df[df['Agent Code'].duplicated(keep=False)]
                                if not duplicate_codes.empty:
                                    duplicate_info = []
                                    for code in duplicate_codes['Agent Code'].unique():
                                        duplicate_rows = duplicate_codes[duplicate_codes['Agent Code'] == code].index
                                        row_numbers = [idx + 2 for idx in duplicate_rows]
                                        duplicate_info.append(f'Agent code "{code}" appears multiple times in rows: {row_numbers}')

                                    errors.extend(duplicate_info)
                                    return None, errors
                                empty_rows = df[df[column].str.strip() == ''].index
                                if len(empty_rows) > 0:
                                    row_numbers = [idx + 2 for idx in empty_rows[:5]]  # Show first 5
                                    errors.append(
                                        f'{column} is required but empty in rows: {row_numbers}'
                                        + ('...' if len(empty_rows) > 5 else '')
                                    )
                                    return None, errors

                                # NEW: Validate Agent Code existence in database
                                # Clean agent codes first
                                df['Agent Code'] = df['Agent Code'].str.strip()

                                # Get all unique agent codes from the DataFrame
                                unique_agent_codes = df['Agent Code'].unique()

                                # Check which agent codes exist in database
                                existing_agent_codes = set(
                                    USER_MODEL.objects.filter(
                                        agent_code__in=unique_agent_codes
                                    ).values_list('agent_code', flat=True)
                                )

                                missing_codes_with_rows = []
                                for index, row in df.iterrows():
                                    agent_code = row['Agent Code']
                                    if agent_code not in existing_agent_codes:
                                        missing_codes_with_rows.append({
                                            'code': agent_code,
                                            'row': index + 2  # +2 for Excel row numbering
                                        })
                                if missing_codes_with_rows:
                                    missing_codes_dict = {}
                                    for item in missing_codes_with_rows:
                                        code = item['code']
                                        if code not in missing_codes_dict:
                                            missing_codes_dict[code] = []
                                        missing_codes_dict[code].append(item['row'])

                                    error_messages = []
                                    for code, rows in missing_codes_dict.items():
                                        if len(rows) <= 3:
                                            error_messages.append(f'Agent code "{code}" not found in database (rows: {rows})')
                                        else:
                                            error_messages.append(
                                                f'Agent code "{code}" not found in database '
                                                f'(rows: {rows[:3]} and {len(rows)-3} more)'
                                            )

                                    if len(error_messages) > 10:
                                        error_messages = error_messages[:10]
                                        error_messages.append('...and more missing agent codes')

                                    errors.extend(error_messages)
                                    return None, errors

                                agent_code_to_user = {}
                                users_queryset = USER_MODEL.objects.filter(agent_code__in=unique_agent_codes)
                                for user in users_queryset:
                                    agent_code_to_user[user.agent_code] = user

                                df['agent'] = df['Agent Code'].map(agent_code_to_user)

                                if df['agent'].isna().any():
                                    errors.append('Internal error: Failed to map some agent codes to users')
                                    return None, errors

                            elif column in ['Top Quartile (MTD)', 'Top Quartile (YTD)']:
                                # Updated valid quartile choices
                                valid_quartile_choices = ['TERMINATED', 'IN', 'OUT']

                                # Clean and standardize values
                                df[column] = df[column].str.strip().str.upper()
                                df[column] = df[column].replace({
                                    'Y': 'IN', 'YES': 'IN', 'T': 'IN', 'TRUE': 'IN', '1': 'IN',
                                    'N': 'OUT', 'NO': 'OUT', 'F': 'OUT', 'FALSE': 'OUT', '0': 'OUT',
                                    'NA': 'OUT', 'N/A': 'OUT', '-': 'OUT', '': 'OUT'
                                })

                                # Check for invalid values
                                invalid_mask = ~df[column].isin(valid_quartile_choices + [''])
                                if invalid_mask.any():
                                    invalid_rows = df[invalid_mask].index
                                    invalid_values = df.loc[invalid_rows, column].unique()
                                    errors.append(
                                        f'{column} contains invalid values: {list(invalid_values)}. '
                                        f'Valid options: {valid_quartile_choices}'
                                    )
                                    return None, errors

                        elif dtype == 'float64':

                            # BLOCK PERSENTAGE VALUE CONVERSION
                            original_values = df[column].copy()
                            numeric_values = pd.to_numeric(df[column], errors='coerce').fillna(0.0)
                            failed_conversion = numeric_values.isna() & original_values.notna() & (original_values.astype(str).str.strip() != '')

                            if failed_conversion.any():
                                invalid_rows = [idx + 2 for idx in df[failed_conversion].index[:5]]
                                invalid_values = original_values[failed_conversion].unique()
                                errors.append(
                                    f'{column} contains non-numeric values: {list(invalid_values)}. '
                                    f'Found in rows: {invalid_rows}'
                                    + ('...' if failed_conversion.sum() > 5 else '')
                                )
                                return None, errors
                            df[column] = numeric_values.fillna(0.0)
                            # ENDBLOCK

                            if column in [
                                'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                                'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'YTD_CASE'
                            ]:
                                negative_mask = df[column] < 0
                                if negative_mask.any():
                                    negative_rows = [idx + 2 for idx in df[negative_mask].index[:5]]
                                    errors.append(
                                        f'{column} contains negative values in rows: {negative_rows}'
                                        + ('...' if negative_mask.sum() > 5 else '')
                                    )
                                    return None, errors

                            # # BLOCK YTD GROWTH BOUND CHECK
                            # elif column == 'YTD Growth':
                            #     # Growth should be between -1.0 and 1.0
                            #     invalid_mask = (df[column] < -1.0) | (df[column] > 1.0)
                            #     if invalid_mask.any():
                            #         invalid_rows = [idx + 2 for idx in df[invalid_mask].index[:5]]
                            #         errors.append(
                            #             f'{column} must be between -1.0 and 1.0 (decimal format). '
                            #             f'Invalid values in rows: {invalid_rows}'
                            #             + ('...' if invalid_mask.sum() > 5 else '')
                            #         )
                            #         return None, errors
                            # # ENDBLOCK

                            elif column == 'YTD Contribution to Unit':
                                # Contribution should be between 0.0 and 1.0
                                invalid_mask = (df[column] < 0.0) | (df[column] > 1.0)
                                if invalid_mask.any():
                                    invalid_rows = [idx + 2 for idx in df[invalid_mask].index[:5]]
                                    errors.append(
                                        f'{column} must be between 0.0 and 1.0 (decimal format). '
                                        f'Invalid values in rows: {invalid_rows}'
                                        + ('...' if invalid_mask.sum() > 5 else '')
                                    )
                                    return None, errors

                    month_cols = [
                        'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                        'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'
                    ]

                    df['month_sum'] = df[month_cols].sum(axis=1)
                    df['ytd_difference'] = abs(df['YTD_CASE'] - df['month_sum'])

                    mismatch_mask = (df['ytd_difference'] > 0.02) & (df['YTD_CASE'] > 0)
                    if mismatch_mask.any():
                        mismatch_rows = [idx + 2 for idx in df[mismatch_mask].index[:5]]
                        errors.append(
                            f'YTD_CASE does not match sum of monthly values in rows: {mismatch_rows}'
                            + ('...' if mismatch_mask.sum() > 5 else '')
                        )
                        return None, errors

                    df = df.drop(['month_sum', 'ytd_difference'], axis=1)

                except Exception as e:
                    errors.append(f'Data type conversion error: {str(e)}')
                    return None, errors

                if validation_errors:
                    error_message = f'Data validation failed:\n\n' + '\n'.join(validation_errors)
                    errors.append(error_message)
                    return None, errors

                # Store the cleaned DataFrame for later use (optional)

            except pd.errors.EmptyDataError:
                errors.append('Excel file is empty or corrupted.')
                return None, errors

            except Exception as e:
                return None, [f'Error reading Excel file: {str(e)}']

        return df, None

    def add_view(self, request, form_url='', extra_context=None):
        if request.method == 'GET':
            return super().add_view(request, form_url, extra_context)

        form = CaseCountImportForm(request.POST)
        df, _errs = self.process_excel_file(request.FILES['excel_file'])

        if _errs:
            [messages.add_message(request, messages.ERROR, _err) for _err in _errs]
        else:
            rows = df.to_dict(orient='records')
            for row in rows:
                agent = row['agent']
                obj, _created = CaseCount.objects.update_or_create(
                    agent=agent,
                    year=request.POST.get('year'),
                    defaults={
                        'year': request.POST.get('year'),
                        'JAN': row['JAN'], 'FEB': row['FEB'],
                        'MAR': row['MAR'], 'APR': row['APR'],
                        'MAY': row['MAY'], 'JUN': row['JUN'],
                        'JUL': row['JUL'], 'AUG': row['AUG'],
                        'SEP': row['SEP'], 'OCT': row['OCT'],
                        'NOV': row['NOV'], 'DEC': row['JUN'],
                        'YTD_CASE': row['YTD_CASE'],
                        'YTD_GROWTH': row['YTD Growth'],
                        'YTD_CONTRIBUTION_TO_UNIT': row['YTD Contribution to Unit'],
                        'TOP_QUARTILE_YTD': row['Top Quartile (YTD)'],
                        'TOP_QUARTILE_MTD': row['Top Quartile (MTD)']
                    }
                )
                print("abc:", _created)
        return redirect(reverse(
            f"admin:{CaseCount._meta.app_label}_{CaseCount._meta.model_name}_changelist"
        ))

    def change_view(self, object, **kwargs):
        return redirect(reverse(
            f"admin:{CaseCount._meta.app_label}_{CaseCount._meta.model_name}_changelist"
        ))
        pass

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
                agent_name,
                agent_code
            )
        return format_html('<strong style="color: #1f2937;">{}</strong>', agent_name)

    @display(description='Year', ordering='year')
    def year_badge(self, obj):
        return format_html(
            '<span style="background: linear-gradient(135deg, #667eea, #764ba2); '
            'color: white; padding: 6px 12px; border-radius: 16px; '
            f'font-size: 12px; font-weight: 600;">{obj.year}</span>',
        )

    @display(description='YTD Cases', ordering='YTD_CASE')
    def ytd_case_formatted(self, obj):
        if obj.YTD_CASE > 0:
            return format_html(
                f'<strong style="color: #059669; font-size: 14px;">{obj.YTD_CASE:.2f}</strong>',

            )
        return format_html('<span style="color: #dc2626;">0.00</span>')

    @display(description='YTD Growth', ordering='YTD_GROWTH')
    def ytd_growth_formatted(self, obj):
        growth_percent = obj.YTD_GROWTH * 100  # Convert to percentage

        if obj.YTD_GROWTH > 0:
            return format_html(
                f'<span style="color: #059669; font-weight: 600;">▲ {growth_percent:.2f}%</span>',
            )
        elif obj.YTD_GROWTH < 0:
            return format_html(
                f'<span style="color: #dc2626; font-weight: 600;">▼ {abs(growth_percent):.2f}%</span>',

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
            f'<span style="color: {color}; font-weight: 600;">{contribution_percent:.2f}%</span>',

        )

    @display(description='MTD Status')
    def top_quartile_mtd_badge(self, obj):
        colors = {
            TopQuartileStatus.IN: ('#10b981', '✓ Top Quartile'),
            TopQuartileStatus.OUT: ('#ef4444', '✗ Below'),
            TopQuartileStatus.NA: ('#6b7280', 'N/A'),
        }
        color, text = colors.get(obj.TOP_QUARTILE_MTD, ('#6b7280', 'Unknown'))

        return format_html(
            f'<span style="background-color: {color}; color: white; padding: 4px 8px; '
            f'border-radius: 12px; font-size: 11px; font-weight: 600;">{text}</span>',
        )

    @display(description='YTD Status')
    def top_quartile_ytd_badge(self, obj):
        colors = {
            TopQuartileStatus.IN: ('#10b981', '✓ Top Quartile'),
            TopQuartileStatus.OUT: ('#ef4444', '✗ Below'),
            TopQuartileStatus.NA: ('#6b7280', 'N/A'),
        }
        color, text = colors.get(obj.TOP_QUARTILE_YTD, ('#6b7280', 'Unknown'))

        return format_html(
            f'<span style="background-color: {color}; color: white; padding: 4px 8px; '
            f'border-radius: 12px; font-size: 11px; font-weight: 600;">{text}</span>',
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
                    F'<span style="color: #1f2937; font-weight: 600;">{month_names[i]}: {month_values[i]:.2f}</span>',

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


