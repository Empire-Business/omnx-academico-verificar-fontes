#!/usr/bin/env python3
"""Confere uma lista de referências em bases públicas e imprime JSON com o semáforo preliminar.

Uso: conferir_referencias.py <arquivo.txt>     (uma referência por linha)

Consulta Crossref, doi.org e DataCite. Sem chave. Biblioteca padrão do Python 3.8 em diante.
Variável opcional CROSSREF_MAILTO: e-mail para o Crossref identificar quem consulta.
Não altera nenhum arquivo.
"""
import datetime as dt
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.IGNORECASE)
ANO_RE = re.compile(r"\b(1[5-9]\d\d|20\d\d)\b")
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
PAGINAS_RE = re.compile(r"\bpp?\.?\s*\d+\s*[-\u2013]\s*\d+", re.IGNORECASE)
MAILTO = os.environ.get("CROSSREF_MAILTO", "").strip()
AGENTE = "omnx-academico-verificar-fontes/1.0" + (" (mailto:%s)" % MAILTO if MAILTO else "")
PAUSA = 0.25
TEMPO_LIMITE = 20
TIPOS_RETRATACAO = {"retraction", "withdrawal", "removal"}
TIPOS_ALERTA = {"expression_of_concern", "expression-of-concern", "partial_retraction", "partial-retraction"}


class ErroDeRede(Exception):
    pass


def imprimir(dados):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(dados, ensure_ascii=False, indent=2))


def get_json(url):
    """Devolve (status, json). 404 volta como (404, None); falha de conexão vira ErroDeRede."""
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "application/json"})
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, None
            if e.code in (429, 500, 502, 503, 504) and tentativa < 2:
                espera = e.headers.get("Retry-After", "")
                time.sleep(min(int(espera), 10) if espera.isdigit() else 2 * (tentativa + 1))
                continue
            raise ErroDeRede("o serviço respondeu com erro %d" % e.code)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            if tentativa < 2:
                time.sleep(2 * (tentativa + 1))
                continue
            raise ErroDeRede(str(getattr(e, "reason", e)))
    raise ErroDeRede("sem resposta")


def limpar_doi(bruto):
    doi = bruto.rstrip(".,;:'”’]")
    while doi.endswith(")") and doi.count(")") > doi.count("("):
        doi = doi[:-1]
    return doi


def tokens(texto):
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return re.findall(r"[a-z0-9]+", sem_acento.lower())


def cobertura(titulo, referencia):
    """Parte das palavras do título da base que aparecem na referência (0 a 1)."""
    base = [t for t in tokens(titulo) if len(t) >= 3]
    if not base:
        return 0.0
    ref = set(tokens(referencia))
    return sum(t in ref for t in base) / len(base)


def anos_crossref(m):
    anos = set()
    for chave in ("issued", "published", "published-print", "published-online"):
        partes = (m.get(chave) or {}).get("date-parts") or [[]]
        if partes[0] and partes[0][0]:
            anos.add(int(partes[0][0]))
    return anos


def do_crossref(m):
    titulo = (m.get("title") or [""])[0]
    autores = [a.get("family") or a.get("name") or "" for a in m.get("author", [])]
    return {
        "fonte": "crossref",
        "titulo": titulo,
        "autores": [a for a in autores if a][:6],
        "revista": (m.get("container-title") or [""])[0],
        "revista_abreviada": (m.get("short-container-title") or [""])[0],
        "ano": min(anos_crossref(m)) if anos_crossref(m) else None,
        "anos_validos": sorted(anos_crossref(m)),
        "issn": m.get("ISSN") or [],
        "editora": m.get("publisher") or "",
        "tipo": m.get("type") or "",
    }


def do_datacite(a):
    titulo = ((a.get("titles") or [{}])[0]).get("title", "")
    autores = [c.get("familyName") or c.get("name") or "" for c in a.get("creators", [])]
    ano = a.get("publicationYear")
    return {
        "fonte": "datacite",
        "titulo": titulo,
        "autores": [x for x in autores if x][:6],
        "revista": a.get("publisher") if isinstance(a.get("publisher"), str) else "",
        "revista_abreviada": "",
        "ano": ano,
        "anos_validos": [ano] if ano else [],
        "issn": [],
        "editora": a.get("publisher") if isinstance(a.get("publisher"), str) else "",
        "tipo": ((a.get("types") or {}).get("resourceTypeGeneral") or "").lower(),
    }


def buscar_candidato(referencia):
    """Procura no Crossref um registro compatível com a referência. Devolve (base, confere, doi, registro) ou None."""
    q = urllib.parse.urlencode({"query.bibliographic": referencia[:300], "rows": 3})
    _, dados = get_json("https://api.crossref.org/works?" + q)
    melhor = None
    for m in (dados or {}).get("message", {}).get("items", []):
        base = do_crossref(m)
        c = confere(base, referencia)
        if melhor is None or c["titulo_cobertura"] > melhor[1]["titulo_cobertura"]:
            melhor = (base, c, m.get("DOI"), m)
    if melhor and melhor[1]["titulo"] == "bate" and melhor[1]["autor"] and melhor[1]["ano"]:
        return melhor
    return None


def anotar_candidato(item, referencia):
    """Em DOI errado: mostra se o trabalho existe com outro DOI, sem mudar a cor."""
    candidato = buscar_candidato(referencia)
    if candidato and candidato[2].lower() != (item["doi"] or "").lower():
        item["candidato_doi"] = candidato[2]
        item["falta"].append("Há um registro compatível com outro DOI (%s): confirme se é o trabalho citado e corrija a referência." % candidato[2])


def retratacoes(m):
    saida = []
    titulo = ((m.get("title") or [""])[0]).strip().lower()
    for u in m.get("updated-by") or []:
        tipo = (u.get("type") or "").lower().replace(" ", "_")
        if tipo in TIPOS_RETRATACAO or tipo in TIPOS_ALERTA:
            saida.append({"tipo": tipo, "doi_aviso": u.get("DOI"), "fonte": u.get("source")})
    if not any(s["tipo"] in TIPOS_RETRATACAO for s in saida) and re.match(r"(retracted|withdrawn)\b", titulo):
        saida.append({"tipo": "retraction", "doi_aviso": None, "fonte": "título do registro"})
    return saida


def confere(base, referencia):
    # DOI, link e páginas têm números e palavras que não são dados da referência
    referencia = PAGINAS_RE.sub(" ", DOI_RE.sub(" ", URL_RE.sub(" ", referencia)))
    titulo_inteiro = cobertura(base["titulo"], referencia)
    titulo_principal = cobertura(re.split(r"[:?]", base["titulo"], 1)[0], referencia)
    titulo = max(titulo_inteiro, titulo_principal)
    ref_tokens = set(tokens(referencia))
    primeiro = tokens(base["autores"][0]) if base["autores"] else []
    autor = all(t in ref_tokens for t in primeiro) if primeiro else None
    anos_ref = {int(a) for a in ANO_RE.findall(referencia)}
    ano = bool(anos_ref & set(base["anos_validos"])) if base["anos_validos"] else None
    revista = None
    if base["revista"]:
        revista = max(cobertura(base["revista"], referencia), cobertura(base["revista_abreviada"], referencia)) >= 0.5
    return {
        "titulo_cobertura": round(titulo, 2),
        "titulo": "bate" if titulo >= 0.8 else ("parcial" if titulo >= 0.5 else "nao_bate"),
        "autor": autor,
        "ano": ano,
        "revista": revista,
    }


def novo_item(n, texto, doi):
    return {"n": n, "referencia": texto, "doi": doi, "base": None, "confere": None, "retratacao": [], "cor": None, "motivos": [], "falta": []}


def com_doi(item, referencia):
    doi = item["doi"]
    caminho = urllib.parse.quote(doi, safe="")
    status, dados = get_json("https://api.crossref.org/works/" + caminho)
    registro = None
    if status == 200:
        registro = dados["message"]
        item["base"] = do_crossref(registro)
        item["retratacao"] = retratacoes(registro)
    else:
        status_dc, dados_dc = get_json("https://api.datacite.org/dois/" + caminho)
        if status_dc == 200:
            item["base"] = do_datacite(dados_dc["data"]["attributes"])
        else:
            status_h, h = get_json("https://doi.org/api/handles/" + caminho)
            if status_h == 404 or not h or h.get("responseCode") != 1:
                item["cor"] = "vermelho"
                item["motivos"].append("DOI inexistente: não está no registro oficial de DOIs (provável invenção ou erro de digitação).")
                anotar_candidato(item, referencia)
                return
            item["cor"] = "amarelo"
            item["motivos"].append("O DOI existe, mas fica em outra agência; os dados não puderam ser comparados.")
            item["falta"].append("Abrir https://doi.org/%s e conferir título, autores e ano." % doi)
            return

    c = confere(item["base"], referencia)
    item["confere"] = c
    motivos_amarelo = []
    if item["retratacao"]:
        tipos = {r["tipo"] for r in item["retratacao"]}
        if tipos & TIPOS_RETRATACAO:
            item["cor"] = "vermelho"
            item["motivos"].append("Artigo retratado ou retirado pela revista (%s)." % ", ".join(sorted(tipos & TIPOS_RETRATACAO)))
            return
        motivos_amarelo.append("Há manifestação de preocupação da revista sobre este artigo.")
    titulo_curto = len([t for t in tokens(item["base"]["titulo"]) if len(t) >= 3]) < 5
    if (c["autor"] is False and (c["titulo"] != "bate" or titulo_curto)) or (c["titulo"] == "nao_bate" and not c["ano"]):
        item["cor"] = "vermelho"
        item["motivos"].append("O DOI pertence a outro trabalho: \"%s\"." % item["base"]["titulo"][:120])
        anotar_candidato(item, referencia)
        return
    if c["titulo"] == "nao_bate":
        motivos_amarelo.append("Título diferente do registrado, mas autor e ano batem (pode ser tradução ou erro de digitação).")
    elif c["titulo"] == "parcial":
        motivos_amarelo.append("Título bate só em parte com o registrado.")
    if c["autor"] is False:
        motivos_amarelo.append("Primeiro autor não confere com a base (%s)." % (item["base"]["autores"][0] if item["base"]["autores"] else "sem autor na base"))
    if c["ano"] is False:
        motivos_amarelo.append("Ano não confere com a base (%s)." % item["base"]["ano"])
    if item["base"]["fonte"] == "crossref" and item["base"]["tipo"] == "posted-content":
        motivos_amarelo.append("Preprint: ainda sem revisão por pares.")
    if item["base"]["fonte"] == "datacite":
        if "preprint" in item["base"]["tipo"]:
            motivos_amarelo.append("Preprint: ainda sem revisão por pares.")
        else:
            motivos_amarelo.append("Registro fora do Crossref (DataCite), de tipo %s: confirme se houve revisão por pares." % (item["base"]["tipo"] or "não informado"))
        item["falta"].append("A retratação não é consultada nesta base: procure aviso na página do trabalho.")
    if motivos_amarelo:
        item["cor"] = "amarelo"
        item["motivos"] += motivos_amarelo
    else:
        item["cor"] = "verde_preliminar"
        item["motivos"].append("DOI existe, dados batem, sem retratação registrada.")
    if c["revista"] is False:
        item["falta"].append("Nome da revista não bateu com a base (%s); pode ser abreviação." % item["base"]["revista"])
    if item["base"]["fonte"] == "crossref":
        item["falta"].append("Conferir a revista e avisos no site oficial (camada 2).")


def sem_doi(item, referencia):
    candidato = buscar_candidato(referencia)
    item["cor"] = "amarelo"
    if candidato:
        item["base"], item["confere"], item["candidato_doi"] = candidato[0], candidato[1], candidato[2]
        item["retratacao"] = retratacoes(candidato[3])
        if any(r["tipo"] in TIPOS_RETRATACAO for r in item["retratacao"]):
            item["cor"] = "vermelho"
            item["motivos"].append("Referência sem DOI, compatível com um artigo retratado (%s)." % candidato[2])
            return
        item["motivos"].append("Referência sem DOI. A base tem um registro compatível (candidato: %s)." % candidato[2])
        item["falta"].append("Confirmar se o candidato é o trabalho citado e acrescentar o DOI.")
    else:
        item["motivos"].append("Referência sem DOI e sem registro compatível no Crossref.")
        item["falta"].append("Procurar pelo título exato (camada 2). Artigo de revista que não aparece em nenhuma base é vermelho; livro, lei, tese, anais e documento oficial podem não ter DOI.")


def processar(linhas):
    itens = []
    for n, referencia in enumerate(linhas, 1):
        achado = DOI_RE.search(referencia)
        doi = limpar_doi(achado.group(0)) if achado else None
        item = novo_item(n, referencia, doi)
        try:
            (com_doi if doi else sem_doi)(item, referencia)
        except ErroDeRede as e:
            item["cor"] = "nao_verificado"
            item["motivos"].append("Não consegui consultar a base (%s)." % e)
            item["falta"].append("Repetir a verificação com internet.")
        itens.append(item)
        time.sleep(PAUSA)
    return itens


def main():
    if len(sys.argv) != 2:
        imprimir({"erro": "Uso: conferir_referencias.py <arquivo.txt> (uma referência por linha)"})
        return 2
    try:
        texto = Path(sys.argv[1]).read_text(encoding="utf-8-sig", errors="replace")
    except OSError as e:
        imprimir({"erro": "Não consegui ler o arquivo: %s" % e})
        return 2
    linhas = [l.strip() for l in texto.splitlines() if re.search(r"[^\W\d_]{3}", l)]
    if not linhas:
        imprimir({"erro": "A lista está vazia."})
        return 2
    itens = processar(linhas)
    por_doi = {}
    for i in itens:
        if i["doi"]:
            por_doi.setdefault(i["doi"].lower(), []).append(i["n"])
    for i in itens:
        repetidos = [n for n in por_doi.get((i["doi"] or "").lower(), []) if n != i["n"]]
        if repetidos:
            i["falta"].append("O mesmo DOI aparece no item %s: uma das referências pode estar errada." % ", ".join(map(str, repetidos)))
    contagem = {}
    for i in itens:
        contagem[i["cor"]] = contagem.get(i["cor"], 0) + 1
    imprimir({
        "data": dt.date.today().isoformat(),
        "camada": "1 (bases públicas)",
        "aviso": "verde_preliminar ainda precisa da conferência da revista (camada 2) e da leitura da fonte.",
        "total": len(itens),
        "contagem": dict(sorted(contagem.items())),
        "itens": itens,
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
