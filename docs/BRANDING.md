# Marca do Komyst

O nome mostrado no aplicativo é **Komyst**. A logo principal usa a imagem K
fornecida pelo usuário: `assets/branding/komyst-logo.png`. A versão usada
pela interface fica em `static/assets/auth/komyst-logo.png`, e o ícone do
aplicativo/navegador é `assets/branding/generated/komyst.ico`.

As telas, mensagens visíveis, traduções, título da janela, versão exibida,
instalador, guia do usuário e documentação passaram a usar Komyst.

Alguns identificadores continuam com o nome antigo por compatibilidade: o
pacote Python `yomu/`, variáveis `YOMU_*`, cabeçalhos internos `X-Yomu-*`, o
diretório de dados `%LOCALAPPDATA%\YomuSekai` e o endereço real do repositório
GitHub. Eles não são nomes de exibição; renomeá-los exige migração coordenada
para manter imports, jobs existentes, autenticação e atualizações funcionando.
O instalador mantém a pasta de dados existente e passa a exibir Komyst.
