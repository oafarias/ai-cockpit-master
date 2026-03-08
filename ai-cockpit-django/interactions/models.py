from django.db import models

class LogInteracao(models.Model):
    session_id = models.CharField(max_length=100)
    message_text = models.TextField()
    ai_response = models.TextField()
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    latency = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False            # Importante: O FastAPI que manda aqui
        db_table = 'logs_interacao' # Nome exato da tabela no Postgres
        verbose_name_plural = "Logs Técnicos"

class ResumoSessao(models.Model):
    session_id = models.CharField(max_length=100, verbose_name="ID da Sessão")
    total_mensagens = models.IntegerField(verbose_name="Qtd Mensagens")
    ultima_interacao = models.DateTimeField(verbose_name="Última Atividade")
    ip_cliente = models.GenericIPAddressField(verbose_name="IP do Usuário")
    latencia_media = models.FloatField(verbose_name="Latência Média (s)")

    class Meta:
        managed = False 
        db_table = 'vw_resumo_sessoes'
        verbose_name = "Relatório de Chat"
        verbose_name_plural = "Relatórios de Chats"

    def __str__(self):
        return self.session_id
