from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import LogInteracao, ResumoSessao

@admin.register(ResumoSessao)
class ResumoSessaoAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'total_mensagens', 'ip_cliente', 'latencia_media', 'ultima_interacao', 'ver_detalhes')
    search_fields = ('session_id',)
    
    def ver_detalhes(self, obj):
        # Gera um link que filtra a tabela de logs original pelo session_id atual
        url = reverse('admin:interactions_loginteracao_changelist') + f'?session_id__exact={obj.session_id}'
        return format_html('<a class="button" href="{}">Abrir Conversa</a>', url)

    ver_detalhes.short_description = "Ações"

@admin.register(LogInteracao)
class LogInteracaoAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'session_id', 'latency', 'message_text')
    list_filter = ('session_id', 'client_ip') # Filtro lateral ajuda na navegação
