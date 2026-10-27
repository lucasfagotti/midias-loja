"""Gera 5 Stories por dia (imagens 1080x1920 em midia/stories/) e coloca no calendario.csv como tipo "story".
Uso: python gerar_stories.py AAAA-MM-DD AAAA-MM-DD   (primeiro e último dia; rodar de novo não duplica)
Grade do dia: 1) dica  2) mito ou verdade  3) post do feed (dia de carrossel) ou um slide antigo
              4) chamada de produto  5) o Reels do dia (dia de Reels) ou uma frase
Os horários mudam um pouco a cada dia e o bot.py ainda soma 0 a 25 min, para não parecer robô.
"""
import os, sys, csv, hashlib, datetime as dt
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
CAL = os.path.join(BASE, "calendario.csv")
OUT = os.path.join(BASE, "midia", "stories")
os.makedirs(OUT, exist_ok=True)
FB, FR = r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"
LAR, ESC, AREIA, CLARO = (238, 77, 45), (31, 41, 55), (246, 236, 226), (255, 220, 210)
W, H = 1080, 1920
ARROBA = "@loja_quelucra"

DICAS = [
    "Antes de baixar o preço, confira quanto sobra depois das taxas. Desconto em cima de margem curta vira prejuízo.",
    "A primeira foto decide o clique. Produto inteiro, fundo limpo e boa luz valem mais que qualquer filtro.",
    "Responda as mensagens rápido. Quem pergunta está quase comprando; quem espera, compra do concorrente.",
    "Coloque no título o que o cliente digita na busca: tipo do produto, característica, cor e material.",
    "Produto parado há mais de 90 dias é dinheiro preso. Monte um kit, faça promoção e devolva esse dinheiro ao giro.",
    "Markup 3x sobre o custo é o padrão. Abaixo de 2,5x, só em promoção ou para desovar estoque parado.",
    "Tabela de medidas na descrição evita troca. Cada troca evitada é frete e margem que ficam com você.",
    "Avaliação negativa: responda com calma, em público, oferecendo solução. Quem lê olha a resposta, não só a nota.",
    "Separe o dinheiro da loja do seu. Sem isso você nunca sabe se a loja dá lucro.",
    "Venda em kit aumenta o ticket: chinelo + meia, bolsa + carteira. O cliente leva mais e o frete sai uma vez só.",
    "Antes de anunciar, veja se o produto já vende sem anúncio. Anúncio acelera o que já funciona.",
    "Faça o fechamento do mês: quanto entrou, quanto saiu, quanto sobrou. São 30 minutos que mudam suas decisões.",
    "Cores e tamanhos como variações do mesmo anúncio juntam vendas e avaliações num lugar só.",
    "Foto no pé ou no corpo vende mais que o produto solto: o cliente se imagina usando.",
    "Despachar no mesmo dia melhora a reputação e diminui cancelamento.",
    "Olhe a curva ABC: poucos produtos fazem a maior parte do faturamento. Nunca deixe faltar esses.",
    "Preço terminado em ,90 parece menor. Só confira se o arredondamento não derrubou sua margem.",
    "Descrição boa responde antes da pergunta: material, forma do tamanho, cuidados e como funciona a troca.",
    "Data comercial se prepara com 30 a 45 dias de antecedência: estoque, fotos e anúncios prontos.",
    "Com markup 3x, o desconto máximo para não ficar abaixo de 2,5x é 16,7%. Passou disso, a margem foi embora.",
    "Olhe os 5 mais vendidos do mês e reponha antes de acabar. Ruptura no campeão de vendas custa caro.",
    "Mensagem simples depois da entrega (\"chegou tudo certo?\") aumenta a chance de avaliação.",
    "Um vídeo curto do produto em uso mostra em 10 segundos o que a foto não mostra.",
    "Anote o motivo de cada devolução. Se o motivo se repete, o problema está no anúncio ou no produto.",
    "A taxa fixa por item pesa mais em produto barato. Às vezes vale vender em kit em vez de unidade.",
    "Frete grátis não é grátis: alguém paga. Coloque na conta antes de definir o preço.",
    "Não compre estoque só porque o fornecedor deu desconto. Compre o que você consegue girar.",
    "Poste com constância. Um post por dia, todo dia, vale mais que dez num dia e nada na semana.",
    "Use o mesmo fundo e o mesmo estilo nas fotos. A loja fica reconhecível no meio da busca.",
    "Separe um valor fixo por mês para anúncio e meça o resultado. Gasto sem medir é aposta.",
    "Antes de entrar num marketplace novo, simule as taxas dele com o seu produto. Cada canal cobra diferente.",
]
MITOS = [  # (afirmação, é verdade?, explicação)
    ("Preço mais baixo sempre vende mais.", False, "Preço baixo sem margem vende e dá prejuízo. Preço certo com anúncio bom vende melhor."),
    ("Faturamento alto quer dizer loja lucrando.", False, "Dá para faturar muito e perder dinheiro. O que importa é o que sobra no fim do mês."),
    ("Responder rápido ajuda a vender.", True, "Quem pergunta está decidindo. Demorar é deixar a venda para outra loja."),
    ("Produto parado não custa nada, ele só está lá.", False, "Ele prende dinheiro que podia estar em produto que gira."),
    ("Uma avaliação negativa acaba com a loja.", False, "Uma resposta educada e com solução passa confiança para quem lê depois."),
    ("O cliente tem 7 dias para desistir de uma compra online.", True, "É o direito de arrependimento (CDC, art. 49), mesmo sem defeito nenhum."),
    ("Produto com defeito só pode ser trocado em até 7 dias.", False, "Defeito tem garantia legal: 30 dias para não duráveis e 90 dias para duráveis (CDC, art. 26)."),
    ("Anúncio pago resolve loja que não vende.", False, "Anúncio leva gente. Se o anúncio do produto não convence, você paga para perder a venda."),
    ("Kit aumenta o ticket médio.", True, "O cliente leva mais numa compra só e o frete se divide entre os itens."),
    ("Desconto de 20% sempre cabe na margem.", False, "Com markup 3x, 20% de desconto deixa o preço abaixo de 2,5x o custo."),
    ("Repetir a mesma palavra várias vezes no título ajuda na busca.", False, "Título bom tem o que o cliente procura, uma vez, de forma clara."),
    ("Tabela de medidas diminui troca.", True, "Quem sabe o tamanho certo antes de comprar não precisa trocar depois."),
    ("Se o concorrente baixou o preço, eu tenho que baixar também.", False, "Veja sua margem primeiro. Às vezes ele está vendendo no prejuízo."),
    ("Postar todo dia ajuda a loja a ser lembrada.", True, "Constância faz o cliente lembrar de você na hora em que precisar."),
    ("Frete grátis é sempre prejuízo.", False, "Se ele estiver na conta do preço, pode até aumentar a venda sem tirar margem."),
    ("Separar conta pessoal e conta da loja é coisa de empresa grande.", False, "É o primeiro passo para saber se a sua loja dá lucro."),
    ("Vídeo do produto em uso costuma vender mais que só foto.", True, "Ele mostra tamanho, caimento e textura de verdade."),
    ("Comprar muito do fornecedor para ganhar desconto sempre compensa.", False, "Se não girar, o desconto vira dinheiro parado na prateleira."),
    ("Poucos produtos fazem a maior parte das vendas.", True, "É a curva ABC. Cuide primeiro desses e nunca deixe faltar."),
    ("Preço que termina em ,90 parece mais barato.", True, "Funciona, mas confira se o arredondamento não comeu a margem."),
    ("Loja pequena não precisa de fluxo de caixa.", False, "Loja pequena é a que mais sente quando o dinheiro acaba antes do mês."),
    ("Data comercial se prepara com antecedência.", True, "Estoque, fotos e preços prontos 30 a 45 dias antes da data."),
    ("Mais fotos no anúncio passam mais confiança.", True, "Detalhe, sola, etiqueta, uso: cada foto responde uma dúvida."),
    ("Cliente não lê descrição.", False, "Quem está em dúvida lê, e é a descrição que tira a dúvida."),
    ("Dá para saber o lucro só olhando o saldo da conta.", False, "O saldo mistura dinheiro de fornecedor, taxas e retiradas. Só o fechamento mostra o lucro."),
    ("Toda venda com cupom é lucro.", False, "Cupom sai da sua margem. Faça a conta antes de criar."),
    ("Mensagem depois da venda aumenta as avaliações.", True, "Um lembrete educado faz o cliente satisfeito avaliar."),
    ("Despachar rápido ajuda a reputação da loja.", True, "Atraso no envio é um dos motivos que mais geram cancelamento e nota baixa."),
    ("Copiar o preço do concorrente é seguro.", False, "O custo dele não é o seu. Calcule o seu preço pelo seu custo."),
    ("Investir pouco em anúncio não adianta nada.", False, "Um valor pequeno e medido mostra o que funciona antes de gastar mais."),
    ("Produto bom se vende sozinho.", False, "Sem foto, título e preço certos, o cliente nem chega a ver o produto."),
]
FRASES = [
    "Vender muito não é o mesmo que lucrar.", "Preço certo não espanta cliente. Espanta prejuízo.",
    "Estoque parado é dinheiro dormindo.", "Quem mede, decide. Quem não mede, chuta.",
    "Cada resposta rápida é uma venda que não foi para o concorrente.", "Constância vence intensidade.",
    "A foto vende antes do preço.", "Desconto sem conta é doação.", "O cliente compra a solução, não o produto.",
    "Margem é o que paga as contas. Faturamento só impressiona.", "Primeiro o lucro, depois a escala.",
    "Fechar o mês é a reunião mais importante da sua loja.", "Seu concorrente não sabe o seu custo.",
    "Uma troca evitada vale mais que uma venda no prejuízo.", "Loja organizada vende com menos esforço.",
    "Quem se prepara antes vende na data. Quem corre depois, liquida.",
]
CTAS = [  # (palavra, pergunta, o que é)
    ("KIT", "Não sabe quanto sobra depois das taxas?", "Calculadora de Markup e Lucro + Guia do Anúncio que Vende"),
    ("AUDITORIA", "Sua loja trava e você não sabe onde?", "Auto-Consultoria: 45 perguntas, nota em 9 áreas e plano de ação"),
    ("CAIXA", "Você sabe se a sua loja dá lucro?", "Kit de Gestão Financeira: fluxo de caixa, DRE e ponto de equilíbrio"),
    ("POSTS", "Sem tempo para criar post?", "Pack com 36 posts prontos no Canva para moda e calçados"),
    ("RELATORIO", "Quer uma análise feita para a sua loja?", "Auditoria Personalizada: relatório em PDF em até 5 dias úteis, sem reunião"),
    ("KIT", "Seu preço está certo ou só parece?", "A calculadora mostra o preço certo e o lucro real de cada produto"),
    ("CAIXA", "O dinheiro some antes do fim do mês?", "Lance entradas e saídas e veja para onde ele vai"),
    ("AUDITORIA", "Quer saber a nota da sua loja?", "Audite a loja sozinho em uma tarde"),
    ("POSTS", "Instagram da loja parado?", "36 posts com fotos reais e legendas prontas, no Canva grátis"),
    ("RELATORIO", "Quer saber o que mudar primeiro?", "Nota da loja, análise dos seus preços e plano de ação em PDF"),
]
SLOTS = [(8, 40), (11, 0), (15, 0), (17, 30), (21, 0)]


def f(p, s): return ImageFont.truetype(p, s)


def wrap(d, t, fo, mw):
    out, cur = [], ""
    for w in t.split():
        x = (cur + " " + w).strip()
        if d.textlength(x, font=fo) <= mw: cur = x
        else: out.append(cur); cur = w
    return out + [cur]


def bloco(d, y, texto, fonte, tam, cor, mw=900, entre=1.18):
    fo = f(fonte, tam)
    for ln in wrap(d, texto, fo, mw):
        d.text((90, y), ln, font=fo, fill=cor); y += int(tam * entre)
    return y


def rodape(d, cor):
    d.text((90, H - 260), ARROBA, font=f(FB, 40), fill=cor)


def st_dica(path, n, texto):
    im = Image.new("RGB", (W, H), LAR); d = ImageDraw.Draw(im)
    d.text((90, 330), f"DICA DO DIA #{n}", font=f(FB, 46), fill=CLARO)
    d.rectangle([90, 400, 250, 410], fill="white")
    bloco(d, 500, texto, FB, 76, "white", entre=1.22)
    rodape(d, CLARO); im.save(path, quality=92)


def st_mito(path, frase, verdade, explica):
    im = Image.new("RGB", (W, H), AREIA); d = ImageDraw.Draw(im)
    d.text((90, 330), "MITO OU VERDADE?", font=f(FB, 56), fill=LAR)
    y = bloco(d, 470, f"\u201c{frase}\u201d", FB, 70, ESC)
    y += 90
    rot = "VERDADE" if verdade else "MITO"
    cor = (34, 139, 84) if verdade else LAR
    fo = f(FB, 64); lw = d.textlength(rot, font=fo)
    d.rounded_rectangle([90, y, 90 + lw + 80, y + 110], radius=24, fill=cor)
    d.text((130, y + 20), rot, font=fo, fill="white")
    bloco(d, y + 170, explica, FR, 52, ESC)
    rodape(d, LAR); im.save(path, quality=92)


def st_frase(path, frase):
    im = Image.new("RGB", (W, H), ESC); d = ImageDraw.Draw(im)
    d.text((90, 560), "\u201c", font=f(FB, 220), fill=LAR)
    bloco(d, 800, frase, FB, 92, "white", entre=1.2)
    rodape(d, CLARO); im.save(path, quality=92)


def st_cta(path, palavra, pergunta, oque):
    im = Image.new("RGB", (W, H), AREIA); d = ImageDraw.Draw(im)
    y = bloco(d, 380, pergunta, FB, 80, ESC)
    y = bloco(d, y + 50, oque, FR, 52, ESC) + 110
    d.text((90, y), "Comente no último post:", font=f(FB, 48), fill=ESC)
    fo = f(FB, 150 if len(palavra) <= 6 else 118); lw = d.textlength(palavra, font=fo)
    d.rounded_rectangle([90, y + 90, 90 + lw + 100, y + 300], radius=36, fill=LAR)
    d.text((140, y + 112), palavra, font=fo, fill="white")
    d.text((90, y + 350), "que eu te mando o link no direct.", font=f(FR, 48), fill=ESC)
    rodape(d, LAR); im.save(path, quality=92)


def st_slide(path, slide, titulo, sub):
    pic = Image.open(slide).convert("RGB")
    fundo = pic.resize((W, H)).filter(ImageFilter.GaussianBlur(40))
    im = Image.blend(fundo, Image.new("RGB", (W, H), ESC), 0.55); d = ImageDraw.Draw(im)
    d.text((90, 250), titulo, font=f(FB, 64), fill="white")
    d.text((90, 335), sub, font=f(FR, 44), fill=CLARO)
    pic.thumbnail((940, 1175))
    x, y = (W - pic.width) // 2, 450
    d.rounded_rectangle([x - 8, y - 8, x + pic.width + 8, y + pic.height + 8], radius=20, fill="white")
    im.paste(pic, (x, y)); im.save(path, quality=92)


def variacao(dia, i):
    """Desloca cada horário de -20 a +20 min, diferente a cada dia."""
    return int(hashlib.md5(f"{dia}{i}".encode()).hexdigest(), 16) % 41 - 20


def main():
    ini, fim = dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2])
    linhas = list(csv.DictReader(open(CAL, encoding="utf-8")))
    ja = {(l["data"], l["hora"]) for l in linhas if l["tipo"] == "story"}
    feed = {l["data"]: l for l in linhas if l["plataforma"] == "instagram" and l["tipo"] in ("carrossel", "reels")}
    agora = dt.datetime.now()
    novas, antigos, n = [], [], 0  # antigos = slides de carrosséis que já foram ao ar
    dia = ini
    while dia <= fim:
        ds, post = dia.isoformat(), feed.get(dia.isoformat())
        n += 1
        k = (dia - dt.date(2026, 10, 27)).days
        for i, (hh, mm) in enumerate(SLOTS):
            t = dt.datetime.combine(dia, dt.time(hh, mm)) + dt.timedelta(minutes=variacao(ds, i))
            hora, arq = f"{t:%H:%M}", None
            if i == 0:
                arq, tit = f"midia/stories/{ds}-1-dica.jpg", "Story: dica do dia"
                st_dica(os.path.join(BASE, arq), k + 1, DICAS[k % len(DICAS)])
            elif i == 1:
                arq, tit = f"midia/stories/{ds}-2-mito.jpg", "Story: mito ou verdade"
                st_mito(os.path.join(BASE, arq), *MITOS[k % len(MITOS)])
            elif i == 2:
                if post and post["tipo"] == "carrossel":
                    s1 = post["arquivos"].split("|")[0].strip()
                    arq, tit = f"midia/stories/{ds}-3-feed.jpg", "Story: post novo no feed"
                    st_slide(os.path.join(BASE, arq), os.path.join(BASE, s1), "SAIU POST NOVO", "Vai lá no perfil ver o carrossel inteiro")
                elif antigos:
                    s = antigos[k % len(antigos)]
                    arq, tit = f"midia/stories/{ds}-3-salvou.jpg", "Story: lembra desse post?"
                    st_slide(os.path.join(BASE, arq), os.path.join(BASE, s), "SALVOU ESSE?", "Tá no perfil, junto com os outros posts")
            elif i == 3:
                arq, tit = f"midia/stories/{ds}-4-cta.jpg", "Story: chamada de produto"
                st_cta(os.path.join(BASE, arq), *CTAS[k % len(CTAS)])
            else:
                if post and post["tipo"] == "reels":
                    arq, tit = post["arquivos"].strip(), "Story: Reels do dia"
                else:
                    arq, tit = f"midia/stories/{ds}-5-frase.jpg", "Story: frase"
                    st_frase(os.path.join(BASE, arq), FRASES[(k // 2) % len(FRASES)])
            if arq and (ds, hora) not in ja and t > agora + dt.timedelta(minutes=10):
                novas.append({"data": ds, "hora": hora, "plataforma": "instagram", "tipo": "story", "arquivos": arq, "legenda": tit})
        if post and post["tipo"] == "carrossel":
            antigos += [a.strip() for a in post["arquivos"].split("|")[1:3]]
        dia += dt.timedelta(days=1)
    with open(CAL, "a", newline="", encoding="utf-8") as fh:
        csv.DictWriter(fh, fieldnames=["data", "hora", "plataforma", "tipo", "arquivos", "legenda"]).writerows(novas)
    print(f"{len(novas)} stories agendados de {ini} a {fim}")


if __name__ == "__main__":
    main()
