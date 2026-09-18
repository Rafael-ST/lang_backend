# Imagens e audios no Railway Bucket

Com `DEBUG=False`, FileField/ImageField usa django-storages com S3.
Com `DEBUG=True`, usa a pasta local `media/`, servida pelo Django em `/media/`,
sem acessar o bucket e sem precisar de credenciais AWS.
Os arquivos estaticos continuam no WhiteNoise, gerados durante o build por
`python manage.py collectstatic --noinput`.

Preencha nas Variables do servico Django no Railway (ou no `.env` apenas
se quiser testar localmente com `DEBUG=False`):

| Variavel Django | Credencial do bucket Railway |
| --- | --- |
| `AWS_STORAGE_BUCKET_NAME` | `BUCKET` (nome S3 real, nao o nome de exibicao) |
| `AWS_ACCESS_KEY_ID` | `ACCESS_KEY_ID` |
| `AWS_SECRET_ACCESS_KEY` | `SECRET_ACCESS_KEY` |
| `AWS_S3_ENDPOINT_URL` | `ENDPOINT`, incluindo `https://` |
| `AWS_S3_REGION_NAME` | `REGION` (normalmente `auto`; copie o valor fornecido) |

No Railway, use referencias ao servico do bucket, por exemplo
`${{lang-media.BUCKET}}`, se ele se chamar `lang-media`.
Nunca envie o `.env` ao GitHub. As credenciais pertencem apenas ao backend.

O `.env` local e os exemplos usam `DEBUG=True`. No Railway, mantenha
`DEBUG=False` e `ENVIRONMENT=production`. Nesse modo, sem as credenciais,
o servidor pode iniciar, mas uploads e URLs de arquivos nao funcionarao.

Os links sao assinados e expiram em uma hora. Consulte novamente a API para
obter links novos; nao grave URLs assinadas em campos JSON ou no banco.
Nao configure dominio publico nem ACL public-read para o bucket privado.

## Arquivos existentes

A configuracao nao transfere os arquivos locais. Copie o conteudo de `media/`
para a raiz do bucket, preservando os caminhos registrados no banco:
`media/cards/audios/hello.mp3` vira `cards/audios/hello.mp3`.
Os registros do banco tambem precisam existir no ambiente de destino.

Depois de preencher as credenciais, reinicie o Django e confira:

1. Uma imagem e um audio existentes, ja copiados para o bucket.
2. Um novo upload, verificando se o objeto aparece no bucket.
3. A URL retornada pela API, que deve apontar ao bucket e conter assinatura.
4. O CSS do admin em `/static/admin/css/base.css`.

Documentacao:
- https://docs.railway.com/storage-buckets
- https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
