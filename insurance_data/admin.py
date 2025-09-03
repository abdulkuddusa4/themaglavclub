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
from unfold.admin import ModelAdmin
from unfold.decorators import display, action
from insurance_data.models import (
    TopQuartileStatus,
    ANP,
    ANPImport,
    CaseCount,
    FYC
)

from insurance_data.forms import ANPImportForm, CaseCountImportForm
import pandas as pd
import os
from insurance_data.insurance_admins.case_count_admin import CaseCountAdminMixin
from insurance_data.insurance_admins.anp_admin import ANPAdminMixin
from insurance_data.insurance_admins.fyc_admin import FYCAdminMixin

USER_MODEL = get_user_model()


@admin.register(ANP)
class ANPAdmin(ANPAdminMixin):
    pass


@admin.register(CaseCount)
class CaseCountAdmin(CaseCountAdminMixin):
    pass


@admin.register(FYC)
class FYCAdmin(FYCAdminMixin):
    pass