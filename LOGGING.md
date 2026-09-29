# Logs e auditoria

O backend adapta o padrão do `viaja-backend`: auditoria persistida no
`django.contrib.admin.models.LogEntry` e diagnóstico com `logging.getLogger(__name__)`.
Não exige dependências ou migrações novas; usa a tabela existente do Django Admin.

## Auditoria

No Django Admin, abra **Administração → Entradas de log**. A consulta permite
filtrar por data, usuário, modelo e ação e pesquisar os detalhes. Os registros
são somente leitura nessa tela; valores são escapados na apresentação HTML.

Cobertura da API:

- Criação, atualização e exclusão de usuários, categorias, níveis, subníveis,
  cards, exercícios, conjuntos de exercícios e imagens de conjuntos.
- Cadastro público, edição e exclusão da própria conta (`usuarios/me`).
- Login com senha e Google concluído, login com senha malsucedido e
  redefinição de senha concluída.
- Recusas de permissão do DRF para usuários autenticados em views com
  `ModelSerializer`.

Cada alteração registra autor, objeto, IP, origem e diferenças antes/depois.
Senhas, tokens, segredos e campos `write_only` têm seus valores ocultados.
Arquivos são representados pelo nome no storage; relações muitos-para-muitos,
pelos IDs. Atualizações sem diferenças não produzem registros.

A escrita e sua auditoria compartilham uma transação: se o registro falhar,
a operação no banco é desfeita. Isso não é uma transação com o storage de arquivos.
O IP vem de `REMOTE_ADDR`, como no Viaja; cabeçalhos de proxy não são aceitos
diretamente como prova de origem.

O cadastro público usa a própria conta criada como autor. Tentativas de login
com usuário desconhecido usam uma conta técnica inativa, sem senha utilizável,
criada sob demanda e excluída da listagem da API. A autoexclusão também usa esse
autor para preservar o registro de exclusão. Outros registros cujo autor seja
um usuário excluído seguem o `CASCADE` nativo de `LogEntry.user`, como no Viaja.

Operações do Django Admin mantêm a auditoria nativa. Ações específicas de
aprendizado (conclusão/reinício de exercícios, cards vistos, consumo de pontos),
foto de perfil, solicitações externas de exclusão, refresh/logout e recusas de
tokens Google não são cobertas pelo mixin de CRUD. Para uma nova ação de escrita,
chame `capturar_estado` e `registrar_alteracao` dentro de `transaction.atomic`,
antes e depois da alteração. Para novos `ModelViewSet`, adicione
`AuditModelMixin` antes da classe do DRF. Escritas diretas via ORM não são
automaticamente auditadas.

## Diagnóstico

Os logs operacionais vão para o console com data, nível, módulo e mensagem.
`LOG_LEVEL` configura o nível (padrão `INFO`; também aceita `DEBUG`, `WARNING`,
`ERROR` e `CRITICAL`). Por exemplo, defina `LOG_LEVEL=WARNING` no ambiente.

Use mensagens parametrizadas, como
`logger.info('Operação concluída (id=%s).', instance.pk)`.
Falhas no envio de e-mail usam mensagens fixas e identificadores internos:
não registre corpo do e-mail, senha, código de redefinição, token, resposta
bruta do provedor ou exceção que possa conter esses dados. O backend de e-mail
de console do Django continua exibindo o conteúdo das mensagens quando
selecionado para desenvolvimento.

## Validação

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test --noinput
```
