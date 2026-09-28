# E-mail via Resend no Railway Hobby

O plano Hobby bloqueia SMTP. Este backend usa `POST https://api.resend.com/emails`.

Depois de publicar o codigo, configure no servico de backend do Railway:

```env
EMAIL_BACKEND=lang_backend.email_backends.ResendEmailBackend
RESEND_API_KEY=re_sua_chave_do_resend
DEFAULT_FROM_EMAIL=Lang <no-reply@seudominio.com>
EMAIL_TIMEOUT=10
```

Use uma chave com permissao de envio para o dominio e um remetente de dominio
verificado no Resend. O remetente de teste `onboarding@resend.dev` tem restricoes
de destinatarios; nao o use para enviar aos usuarios em producao.
Nao salve a chave no repositorio. As variaveis `EMAIL_HOST`, `EMAIL_PORT`,
`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` e `EMAIL_USE_TLS` nao sao usadas por este backend.

Faca o deploy e solicite um novo codigo de recuperacao. Confira os logs do
backend e o status de entrega no painel do Resend. A API aceitar o e-mail nao
garante que ele chegou a caixa de entrada. O endpoint mantem a resposta generica
para nao revelar se uma conta existe, inclusive quando o envio falha.

O timeout limita a espera das operacoes de rede. Ele nao corrige erros de chave,
dominio ou remetente. O backend atende mensagens de texto e HTML, sem anexos.

Referencias:
- https://docs.railway.com/networking/outbound-networking
- https://resend.com/docs/api-reference/emails/send-email
