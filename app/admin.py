import json

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.utils.html import format_html, format_html_join

from app.log_actions import ACESSO_NEGADO, LOG_ACTION_CHOICES, LOGIN_FALHOU


class LogActionFilter(admin.SimpleListFilter):
    title = "tipo de ação"
    parameter_name = "action_flag"

    def lookups(self, request, model_admin):
        return LOG_ACTION_CHOICES

    def queryset(self, request, queryset):
        value = self.value()
        if value in {str(flag) for flag, _ in LOG_ACTION_CHOICES}:
            return queryset.filter(action_flag=int(value))
        return queryset


class LogEntryAdmin(admin.ModelAdmin):
    list_display = ("action_time", "user", "content_type", "object_repr", "tipo_acao", "change_message")
    list_filter = ("action_time", "user", "content_type", LogActionFilter)
    search_fields = ("object_repr", "user__email", "change_message")
    list_select_related = ("user", "content_type")
    ordering = ("-action_time", "-pk")
    fields = (
        "action_time", "user", "content_type", "object_id",
        "object_repr", "tipo_acao", "detalhes",
    )
    readonly_fields = fields

    @admin.display(description="Tipo de ação", ordering="action_flag")
    def tipo_acao(self, obj):
        return dict(LOG_ACTION_CHOICES).get(obj.action_flag, str(obj.action_flag))

    @admin.display(description="Detalhes")
    def detalhes(self, obj):
        try:
            dados = json.loads(obj.change_message)
        except (ValueError, TypeError):
            return obj.get_change_message()
        if obj.action_flag == ACESSO_NEGADO and isinstance(dados, dict):
            return format_html(
                "<p>{}</p><p>API: {} {}</p><p>Permissões exigidas: {}</p><p>IP: {}</p>",
                dados.get("descricao", ""), dados.get("metodo", ""),
                dados.get("caminho", ""),
                ", ".join(dados.get("permissoes_exigidas", [])), dados.get("ip", ""),
            )
        if obj.action_flag == LOGIN_FALHOU and isinstance(dados, dict):
            return format_html(
                "<p>{}</p><p>Identificador informado: {}</p><p>Motivo: {}</p><p>IP: {}</p>",
                dados.get("descricao", ""), dados.get("identificador", ""),
                dados.get("motivo_descricao", ""), dados.get("ip", ""),
            )
        if not isinstance(dados, dict) or not isinstance(dados.get("alteracoes"), dict):
            return obj.get_change_message()
        linhas = []
        for campo, valores in dados["alteracoes"].items():
            if not isinstance(valores, dict):
                continue
            if valores.get("valores_ocultos"):
                antes = depois = "Valor oculto (campo alterado)"
            else:
                antes = json.dumps(valores.get("antes"), ensure_ascii=False)
                depois = json.dumps(valores.get("depois"), ensure_ascii=False)
            linhas.append((campo, antes, depois))
        return format_html(
            "<p>{} — IP: {}</p><table><thead><tr><th>Campo</th>"
            "<th>Antes</th><th>Depois</th></tr></thead><tbody>{}</tbody></table>",
            dados.get("descricao", "Alteração pela API"), dados.get("ip", ""),
            format_html_join("", "<tr><td>{}</td><td>{}</td><td>{}</td></tr>", linhas),
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(LogEntry, LogEntryAdmin)
