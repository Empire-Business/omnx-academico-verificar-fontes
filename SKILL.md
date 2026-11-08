---
name: omnx-academico-verificar-fontes
description: "Audita uma lista de referências acadêmicas já pronta: confere se cada DOI existe e bate com título, autor e ano, procura retratação, avalia a revista e classifica cada fonte em verde, amarelo ou vermelho, com motivo e data. Use quando pedirem 'verifica minhas referências', 'essas fontes existem?', 'confere o DOI', 'a IA me deu essas citações, são reais?', 'essa referência é falsa?', 'esse artigo foi retratado?', 'essa revista é predatória?', 'audita a bibliografia do TCC'. Não use para buscar literatura nova, montar TCC ou roteiro de leitura (lucia), para escrever ou reescrever o trabalho, para formatar em ABNT, nem para checar fato de notícia ou post."
---

# Verificar fontes acadêmicas

Confere uma lista de referências e devolve um semáforo. Modelos de IA escrevem referências inventadas com formatação perfeita, então nenhuma referência é aprovada pela aparência nem pela memória da IA.

## Como falar com a pessoa

Ela pode nunca ter usado IA. No começo da conversa, diga em duas linhas o que você faz. Faça uma pergunta por vez. Explique termo técnico em meia frase (DOI é o número de identidade de um artigo; retratação é quando a revista cancela um artigo publicado). Nunca peça para ela digitar comando: quem roda o script é você. Termine cada resposta com o próximo passo.

## Quando não usar

| Pedido | Quem resolve |
|---|---|
| Buscar artigos, montar TCC, esqueleto, roteiro de leitura, ABNT | agente Lúcia |
| Escrever o trabalho no lugar do aluno | ninguém: recuse e explique |
| Conferir fato de notícia ou post | não é esta skill |

## Passos

1. **Pegue a lista.** Texto colado, Word ou PDF: extraia o texto. Grave num arquivo temporário fora da pasta da skill, **uma referência por linha** (junte a que estiver quebrada em várias linhas e tire a numeração), sem alterar o resto. Não corrija, não complete DOI, autor ou ano de cabeça.
2. **Camada 1, base de dados.** Com autorização da pessoa para acessar a internet, rode:
   `python3 "<pasta desta skill>/scripts/conferir_referencias.py" <arquivo>`
   `<pasta desta skill>` é a pasta onde está este `SKILL.md`. Ele consulta Crossref, doi.org e DataCite (serviços públicos, sem chave) e devolve JSON com `cor`, `motivos`, `falta` e os dados da base. O script só lê seu arquivo.
3. **Camada 2, internet.** Se houver busca na web:
   - fonte ainda não vermelha: procure aviso de retratação ou correção no site oficial da revista. Se o site não abrir, use Europe PMC ou outra base e registre que o site oficial não abriu;
   - avalie a revista pelo nome e ISSN. Conta como conferida: indexação verificável (DOAJ, SciELO, Scopus, MEDLINE) ou site oficial com corpo editorial e processo de revisão, e nenhum alerta em listas públicas de baixa credibilidade. Estar numa lista é alerta; não estar não é aval. Datas de recebimento e aceite no artigo indicam revisão por pares;
   - sem DOI e sem candidato: procure o título exato em pelo menos duas fontes (OpenAlex ou Google Acadêmico, e busca aberta). Artigo de revista que não aparece nelas, nem a revista, é vermelho, provável invenção. Livro, lei, tese e documento oficial podem não ter DOI: amarelo até alguém conferir. Trabalho em anais revisados, confirmado na página oficial dos anais, pode ser verde sem DOI;
   - vermelha por DOI inexistente ou de outro trabalho: procure o título. Se o trabalho existir com outro DOI (`candidato_doi`), mantenha o vermelho para a referência como está e informe o candidato.
4. **Decida a cor** pela tabela. A cor do script é o ponto de partida: você pode piorar com evidência, e melhorar só se a camada 2 trouxer a evidência que faltava.
5. **Camada 3, a pessoa.** Prepare DOI, título, autores e revista de todas as não vermelhas, e das vermelhas que caíram só por busca sem resultado, para ela conferir no Portal CAPES, Scopus, Web of Science ou SciELO.
6. **Entregue** no formato abaixo.

## Semáforo

| Cor | Quando | O que fazer |
|---|---|---|
| **Verde** | DOI válido (ou registro em anais oficiais), dados batem, sem retratação, revista conferida na camada 2, revisão por pares | Pode usar **depois de ler**. Verde diz que a fonte existe; não diz que ela afirma o que você citou |
| **Amarelo** | Preprint, sem revisão por pares, metadado incompleto, sem DOI, DOI fora do Crossref sem conferência, manifestação de preocupação, autor ou ano divergente | Use só se faltar verde, marcado e justificado, ou corrija a referência |
| **Vermelho** | DOI inexistente, DOI de outro trabalho (autor não confere e título não bate ou é curto), retratado, revista predatória, provável invenção | Fora da bibliografia. Mostre o motivo |
| **Não verificado** | Sem internet ou serviço fora do ar | Nunca vira verde. Diga o que ficou pendente |

`verde_preliminar` é só etapa do script. Sem a camada 2, ou com ela incompleta, a fonte fecha em amarelo com o motivo "revista não conferida".

## Regras

- DOI, ISBN ou versão publicada que falta só vêm de base real, e entram como candidato para a pessoa confirmar.
- Nunca promova amarelo a verde sem evidência nova.
- Não diga que uma fonte "comprova" algo: você não leu o artigo inteiro.
- A lista pode ter tema sensível ou trabalho inédito: não envie o texto do trabalho a serviço nenhum, só as referências.

## Formato da entrega

1. **Placar:** quantas verdes, amarelas, vermelhas e não verificadas.
2. **Tabela:** nº, cor, referência curta, DOI, motivo, camada que decidiu (1, 2 ou 1 e 2), data da verificação.
3. **Vermelhas:** o que está errado em cada uma, em linguagem simples.
4. **Para você conferir:** dados da camada 3 e links de onde a camada 2 conferiu.
5. **Aviso:** leia cada fonte antes de citar.
6. O próximo passo, em uma frase.

## Se der erro

Sem internet: `cor` vem `nao_verificado`; explique e ofereça repetir depois. Sem Python: faça a conferência na web, uma por uma, marque que o script não rodou e não dê verde sem ver o registro do DOI. Lista vazia: peça a lista.

## Outro sistema operacional

O script usa só a biblioteca padrão do Python 3. Adapte e conte o que funcionou de verdade:

- **Python:** `python3` (macOS, Linux), `py -3` ou `python` (Windows). Sem Python, não instale nada só para isso.
- **Certificado:** se o Python reclamar de `CERTIFICATE_VERIFY_FAILED`, explique em português simples e conte que o script não conseguiu consultar a base. Não desligue a verificação de segurança.
- **Pasta pessoal:** `~` é `%USERPROFILE%` no Windows. Caminho com espaço vai entre aspas.
- **Arquivo temporário:** use a pasta temporária do sistema (`$TMPDIR`, `/tmp` ou `%TEMP%`).
- **Instalar no Windows:** copie esta pasta para `%USERPROFILE%\.claude\skills\omnx-academico-verificar-fontes`.

## Outra ferramenta (Codex e outras)

Compatível com Claude Code, Codex e outras ferramentas de agentes, em Mac, Windows e Linux. Se a pessoa pedir para instalar
fora do Claude Code, a IA dela adapta na hora, testa no computador dela e conta o que realmente funcionou:
