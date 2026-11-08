# omnx-academico-verificar-fontes

Guia visual: abra o `COMO-FUNCIONA.html` desta pasta (dois cliques; funciona sem internet).

Audita uma lista de referências já pronta. Confere se cada DOI (o número de identidade de um artigo) existe e bate com título, autor e ano, procura retratação, avalia a revista e classifica cada fonte em verde, amarelo ou vermelho, com motivo e data.

## O que ela não faz

- Não busca artigos novos nem monta TCC ou roteiro de leitura: isso é do agente **Lúcia**.
- Não escreve o trabalho.
- Verde quer dizer que a fonte existe e passou nas checagens. Quem confirma se ela diz o que foi citado é você, lendo.

## Como instalar

**Direto do GitHub:** no Claude Code, diga: "Instale a skill a partir de https://github.com/Empire-Business/omnx-academico-verificar-fontes". Para atualizar, diga: "Atualize a skill a partir de https://github.com/Empire-Business/omnx-academico-verificar-fontes". A IA baixa e copia os arquivos.

Se você já baixou esta pasta:

1. Abra o Claude Code (no aplicativo do Claude, aba **Code**, ambiente **Local**).
2. Escreva: **"Instale a skill que está nesta pasta: `<caminho desta pasta>`"**.
3. Você vai ver a IA copiando os arquivos. Não precisa digitar comando nenhum.
4. Abra uma conversa nova e faça um pedido, como nos exemplos abaixo.

### Instalar à mão

- **Mac ou Linux:** rode `bash install.sh` a partir desta pasta. A skill é copiada para `~/.claude/skills/omnx-academico-verificar-fontes`.
- **Windows:** copie esta pasta para `%USERPROFILE%\.claude\skills\omnx-academico-verificar-fontes`, ou peça para a IA fazer isso. O `install.sh` não é usado no Windows.
- **Outra ferramenta (Codex e outras):** ainda **não foi testada no Codex**. Peça para a IA da ferramenta seguir a seção "Outra ferramenta (Codex e outras)" do `SKILL.md` e contar o que funcionou.

Precisa de Python 3 para rodar o script. Se não tiver, a skill avisa e segue pela leitura, sem contagem automática. Testada só no Mac até agora.

## Como pedir

- "A IA me deu essas referências para o TCC. Elas existem?"
- "Audita a bibliografia do meu artigo."
- "Esse artigo foi retratado? (cole a referência)"

## O que tem na pasta

| Arquivo | Para que serve |
|---|---|
| `SKILL.md` | o passo a passo que a IA segue |
| `scripts/conferir_referencias.py` | consulta bases públicas (Crossref, doi.org, DataCite); não precisa de chave |
| `COMO-FUNCIONA.html` | guia visual |
| `install.sh` | instalação no Mac ou Linux |

## Versões

- 1.0 (08/11/2026): primeira versão.
