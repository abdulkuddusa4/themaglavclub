from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.core.validators import MinValueValidator
from django.core.validators import FileExtensionValidator
import os


class TopQuartileStatus(models.TextChoices):
    """Observed statuses; extend as needed."""
    TERMINATED = "TERMINATED", "TERMINATED"
    YES = "YES", "YES"
    NO = "NO", "NO"
    NA = "N/A", "N/A"


class CaseCount(models.Model):
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="case_performance",
        limit_choices_to={"agent_code__isnull": False},  # ensures agent_code is set
    )

    year = models.PositiveSmallIntegerField(db_index=True)

    TOP_QUARTILE_MTD = models.CharField(
        max_length=20,
        choices=TopQuartileStatus.choices,
        default=TopQuartileStatus.NA,
    )
    TOP_QUARTILE_YTD = models.CharField(
        max_length=20,
        choices=TopQuartileStatus.choices,
        default=TopQuartileStatus.NA,
    )

    JAN = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    FEB = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    MAR = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    APR = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    MAY = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    JUN = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    JUL = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    AUG = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    SEP = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    OCT = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    NOV = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    DEC = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    YTD_CASE = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    YTD_GROWTH = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=Decimal("0.0000"),
        validators=[MinValueValidator(Decimal("-1.0")), MaxValueValidator(Decimal("1.0"))],
    )
    YTD_CONTRIBUTION_TO_UNIT = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=Decimal("0.0000"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("1.0"))],
    )

    class Meta:
        db_table = "agent_case_performance"
        unique_together = ("agent", "year")
        indexes = [
            models.Index(fields=["year", "agent"]),
            models.Index(fields=["TOP_QUARTILE_MTD"]),
            models.Index(fields=["TOP_QUARTILE_YTD"]),
        ]

    def __str__(self) -> str:
        return f"{self.agent} ({self.year})"

    @property
    def sum_of_months(self) -> Decimal:
        """Sum JAN..DEC (useful cross-check against YTD_CASE)."""
        return sum([
            self.JAN, self.FEB, self.MAR, self.APR, self.MAY, self.JUN,
            self.JUL, self.AUG, self.SEP, self.OCT, self.NOV, self.DEC
        ], Decimal("0.00"))

    @staticmethod
    def parse_percent_to_fraction(value) -> Decimal:
        """Convert '12%' or '-100%' into a fraction (0.12, -1.0)."""
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        s = str(value).strip().replace("%%", "%")
        if s.endswith("%"):
            s = s[:-1].strip()
            return (Decimal(s) / Decimal("100")).quantize(Decimal("0.0001"))
        return Decimal(s)

    class Meta:
        verbose_name = "Case Count"
        verbose_name_plural = "Case Counts"


class CaseCountImport(models.Model):
    year = models.IntegerField()
    excel_file = models.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])],
        help_text="Upload Excel file with ANP data"
    )


def upload_to_path(instance, filename):
    """Custom upload path for files"""
    return f'uploads/{instance.month_year.year}/{instance.month_year.month:02d}/{filename}'


from django.db import models
from django.core.validators import FileExtensionValidator
import os


class ANP(models.Model):
    agent_name = models.CharField(max_length=255, verbose_name="Agent Name")
    life_rp = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Life RP")
    life_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Life SP")
    health_shield = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Health Shield")
    pa = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="PA")
    cs = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="CS")
    total_anp = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total ANP")
    
    # Date fields
    year = models.IntegerField()
    month = models.IntegerField(choices=[(i, f"{i:02d}") for i in range(1, 13)])
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', '-month', 'agent_name']
        verbose_name = "ANP Record"
        verbose_name_plural = "ANP Records"
        unique_together = ['agent_name', 'year', 'month']

    def __str__(self):
        return f"{self.agent_name} - {self.month:02d}/{self.year}"

    @property
    def month_year_display(self):
        months = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ]
        return f"{months[self.month-1]} {self.year}"


def upload_excel_path(instance, filename):
    """Custom upload path for Excel files"""
    return f'anp_imports/{instance.year}/{instance.month:02d}/{filename}'


class ANPImport(models.Model):
    """Model to track Excel imports"""
    excel_file = models.FileField(
        upload_to=upload_excel_path,
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])],
        help_text="Upload Excel file with ANP data"
    )
    year = models.IntegerField(verbose_name="Year")
    month = models.IntegerField(
        choices=[(i, f"{i:02d} - {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i-1]}") for i in range(1, 13)],
        verbose_name="Month"
    )
    imported_at = models.DateTimeField(auto_now_add=True)
    records_imported = models.IntegerField(default=0)
    import_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-imported_at']
        verbose_name = "ANP Excel Import"
        verbose_name_plural = "ANP Excel Imports"

    def __str__(self):
        return f"Import {self.month:02d}/{self.year} - {self.records_imported} records"
