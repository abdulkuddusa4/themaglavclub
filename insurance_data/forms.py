from django import forms
from django.core.exceptions import ValidationError
from .models import ANPImport, ANP, CaseCountImport
import pandas as pd
from datetime import datetime


class ANPImportForm(forms.ModelForm):
    class Meta:
        model = ANPImport
        fields = '__all__'
        widgets = {
            'excel_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.xlsx,.xls',
                'style': '''
                    background: linear-gradient(135deg, #667eea, #764ba2) !important;
                    color: white !important;
                    border: none !important;
                    padding: 12px 20px !important;
                    border-radius: 8px !important;
                    font-weight: 600 !important;
                    cursor: pointer !important;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
                '''
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2020,
                'max': 2030,
                'value': datetime.now().year
            }),
            'month': forms.Select(attrs={
                'class': 'form-control'
            }),
            'import_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional notes about this import...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].initial = datetime.now().year
        self.fields['month'].initial = datetime.now().month

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')

        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError('Excel file size must not exceed 5MB.')

            # Validate Excel file structure
            try:
                df = pd.read_excel(file)
                required_columns = [
                    # 'Agent Name', 'Life RP', 'Life SP', 'PA', 'CS',
                    # 'Health Shield', 'Total ANP', 'Agent Code'
                ]

                df.columns = df.columns.str.strip()
                missing_columns = []

                for col in required_columns:
                    if col not in df.columns:
                        missing_columns.append(col)

                if missing_columns:
                    raise ValidationError(
                        f'Missing required columns: {", ".join(missing_columns)}. '
                        f'Found columns: {", ".join(df.columns.tolist())}'
                    )

                if len(df) == 0:
                    raise ValidationError('Excel file appears to be empty.')

            except pd.errors.EmptyDataError:
                raise ValidationError('Excel file is empty or corrupted.')
            except Exception as e:
                raise ValidationError(f'Error reading Excel file: {str(e)}')

        return file


class ANPForm(forms.ModelForm):
    class Meta:
        model = ANP
        fields = '__all__'
        widgets = {
            'agent_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter agent name'
            }),
            'life_rp': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'life_sp': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01'
            }),
            'health_shield': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'pa': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'cs': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'total_anp': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1111,
                'max': 9999
            }),
            'month': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class CaseCountImportForm(forms.ModelForm):
    class Meta:
        # model = CaseCountImport
        model = CaseCountImport
        fields = '__all__'
        widgets = {
            'excel_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.xlsx,.xls',
                'style': '''
                    background: linear-gradient(135deg, #667eea, #764ba2) !important;
                    color: white !important;
                    border: none !important;
                    padding: 12px 20px !important;
                    border-radius: 8px !important;
                    font-weight: 600 !important;
                    cursor: pointer !important;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
                '''
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1111,
                'max': 9999,
                'value': datetime.now().year
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].initial = datetime.now().year

    def clean(self):
        pass



    def clean_excel_file_with_schema(self):
        return super().clean_excel_file_with_schema()
        """Alternative implementation using explicit schema validation"""
        file = self.cleaned_data.get('excel_file')
        if file:
            if file.size > 20 * 1024 * 1024:
                raise ValidationError('Excel file size must not exceed 20MB.')

            try:
                schema = {
                    'columns': {
                        'Agent Name': {'type': str, 'required': True, 'nullable': False},
                        'Agent Code': {'type': str, 'required': True, 'nullable': False},
                        'JAN': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'FEB': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'MAR': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'APR': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'MAY': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'JUN': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'JUL': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'AUG': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'SEP': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'OCT': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'NOV': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'DEC': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'TOP_QUARTILE_MTD': {
                            'type': str,
                            'choices': ['TERMINATED', 'YES', 'NO', 'N/A'],
                            'default': 'N/A'
                        },
                        'TOP_QUARTILE_YTD': {
                            'type': str,
                            'choices': ['TERMINATED', 'YES', 'NO', 'N/A'], 
                            'default': 'N/A'
                        },
                        'YTD_CASE': {'type': float, 'min_value': 0.0, 'default': 0.0},
                        'YTD_GROTH': {'type': float, 'min_value': -1.0, 'max_value': 1.0, 'default': 0.0},
                        'YTD_CONTRIBUTION_TO_UNIT': {'type': float, 'min_value': 0.0, 'max_value': 1.0, 'default': 0.0}
                    }
                }

                df = pd.read_excel(file)
                df.columns = df.columns.str.strip()

                # Validate schema
                errors = []

                # Check required columns
                required_cols = list(schema['columns'].keys())
                missing_cols = set(required_cols) - set(df.columns)
                if missing_cols:
                    errors.append(f'Missing columns: {sorted(missing_cols)}')

                if not errors:
                    for col_name, col_schema in schema['columns'].items():
                        if col_name in df.columns:
                            col_type = col_schema['type']

                            if col_type == str:
                                df[col_name] = df[col_name].astype('string').fillna(col_schema.get('default', ''))

                                if col_schema.get('required') and col_schema.get('nullable') is False:
                                    empty_rows = df[df[col_name].str.strip() == ''].index + 2
                                    if len(empty_rows) > 0:
                                        errors.append(f'{col_name} required but empty in rows: {empty_rows.tolist()[:5]}')

                                if 'choices' in col_schema:
                                    df[col_name] = df[col_name].str.upper().str.strip()
                                    invalid_mask = ~df[col_name].isin(col_schema['choices'] + [''])
                                    if invalid_mask.any():
                                        errors.append(f'{col_name} invalid values. Must be: {col_schema["choices"]}')

                            elif col_type == float:
                                df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(col_schema.get('default', 0.0))

                                if 'min_value' in col_schema:
                                    invalid_mask = df[col_name] < col_schema['min_value']
                                    if invalid_mask.any():
                                        errors.append(f'{col_name} values below minimum {col_schema["min_value"]}')

                                if 'max_value' in col_schema:
                                    invalid_mask = df[col_name] > col_schema['max_value']
                                    if invalid_mask.any():
                                        errors.append(f'{col_name} values above maximum {col_schema["max_value"]}')

                if errors:
                    raise ValidationError('\n'.join(errors))

                self.cleaned_dataframe = df

            except ValidationError:
                raise
            except Exception as e:
                raise ValidationError(f'Error processing Excel file: {str(e)}')

        return file


class FYCImportForm(forms.ModelForm):
    class Meta:
        # model = CaseCountImport
        model = CaseCountImport
        fields = '__all__'
        widgets = {
            'excel_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.xlsx,.xls',
                'style': '''
                    background: linear-gradient(135deg, #667eea, #764ba2) !important;
                    color: white !important;
                    border: none !important;
                    padding: 12px 20px !important;
                    border-radius: 8px !important;
                    font-weight: 600 !important;
                    cursor: pointer !important;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
                '''
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1111,
                'max': 9999,
                'value': datetime.now().year
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].initial = datetime.now().year

    def clean(self):
        pass


class FYCImportForm(forms.ModelForm):
    class Meta:
        # model = CaseCountImport
        model = CaseCountImport
        fields = '__all__'
        widgets = {
            'excel_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.xlsx,.xls',
                'style': '''
                    background: linear-gradient(135deg, #667eea, #764ba2) !important;
                    color: white !important;
                    border: none !important;
                    padding: 12px 20px !important;
                    border-radius: 8px !important;
                    font-weight: 600 !important;
                    cursor: pointer !important;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
                '''
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1111,
                'max': 9999,
                'value': datetime.now().year
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].initial = datetime.now().year

    def clean(self):
        pass