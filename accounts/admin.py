from unfold import admin as unfold_admin
from django.contrib import admin, messages
from .models import JTUser


@admin.register(JTUser)
class JTUserAdmin(unfold_admin.ModelAdmin):
    list_display = (
        "email", "email_verified",
    )

    def has_module_permission(self, request, obj=None):
        return request.user.is_staff

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs |= qs.filter(
            agency=None
        )
        qs |= qs.filter(id=request.user.id)
        if request.user.is_staff and not request.user.is_superuser:
            messages.info(
                request,
                "Agents At your company With their email verified"
                "are shown here."
            )
            return qs.filter(
                is_staff=False,
                is_superuser=False
            )

        messages.info(
            request,
            "Agents  At your company."
        )
        return qs

    def get_readonly_fields(self, request, obj=None):
        return [
            'password',
            'agency',
            'username',
            "email_verified"
        ]

    # override changelist_view to add the message
    # def changelist_view(self, request, extra_context=None):
    #     if request.user.is_superuser:
    #         messages.info(request, "all the ")
    #     else:
    #         messages.info(
    #             request,
    #             "Agents With their email verified are shown here."
    #         )
    #     return super().changelist_view(request, extra_context)
    pass