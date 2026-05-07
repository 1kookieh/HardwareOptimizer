# Ícones de jogos

Coloque aqui os arquivos PNG ou SVG que serão exibidos como ícone em
cada card de jogo na tela inicial. O nome do arquivo precisa bater com
a chave do jogo definida em `app/models/profile.py`:

| Chave              | Arquivo esperado            |
| ------------------ | --------------------------- |
| `valorant`         | `valorant.png`  ou `.svg`   |
| `league_of_legends`| `league_of_legends.png`     |
| `cod_warzone`      | `cod_warzone.png`           |
| `marvel_rivals`    | `marvel_rivals.png`         |
| `fortnite`         | `fortnite.png`              |
| `cs2`              | `cs2.png`                   |

Para jogos personalizados adicionados pelo usuário, o nome do arquivo
deve usar a mesma chave gerada (slug do nome). Resolução recomendada:
**64×64 pixels** com fundo transparente. SVG também é aceito.

Quando o arquivo não existir, o card usa um emoji + sigla curta como
fallback automaticamente.

> **Importante:** logos de jogos costumam ser marcas registradas. Use
> apenas arquivos que você tem direito de redistribuir, ou mantenha a
> pasta vazia e use o fallback.
