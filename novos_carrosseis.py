"""Carrosséis dos produtos novos (06–11), no mesmo visual do gerar_conteudo.py. Saída: midia/<id>_N.jpg"""
import os, sys
BASE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(BASE, "gerar_conteudo.py"), encoding="utf-8").read()
sys.argv = [sys.argv[0]]
exec(src[:src.index("KIT, AUTO, FIN")])  # só as funções de desenho (capa, slide_txt, slide_img, cta)

def capa_produto(pasta):
    return f"{P}/{pasta}/capa-kiwify.png"

N = [  # (id, kicker, gancho, slides, palavra, produto)
 ("lanc-estoque", "ESTOQUE", "Quanto do seu dinheiro está parado na prateleira agora?",
  [("O que a planilha mostra", ["Dinheiro total em estoque", "Quanto está travado em produto parado", "Curva ABC automática", "Quanto repor de cada item"]),
   ("Estoque que Gira", capa_produto("06-estoque-que-gira"))], "ESTOQUE", "link da planilha Estoque que Gira"),
 ("lanc-ml", "MERCADO LIVRE 2026", "As taxas mudaram. O seu preço acompanhou?",
  [("O que a calculadora faz", ["Sugere o preço pelo markup (3x, mínimo 2,5x)", "Calcula comissão, tarifa, frete, imposto e Ads", "Avisa o degrau dos R$ 79", "Compara Clássico x Premium"]),
   ("Kit Vendedor Mercado Livre 2026", capa_produto("07-kit-mercado-livre"))], "ML", "link do Kit Vendedor Mercado Livre"),
 ("lanc-respostas", "ATENDIMENTO", "Pare de responder cliente do zero",
  [("122 mensagens prontas", ["Pré-venda, pedido e rastreio", "Trocas e devoluções (o que a lei garante)", "Respostas a avaliações", "Recuperação de vendas"]),
   ("Respostas Prontas", capa_produto("08-respostas-prontas"))], "RESPOSTAS", "link do pack Respostas Prontas"),
 ("lanc-reels", "VÍDEOS", "10 Reels com os produtos da sua loja",
  [("Como funciona", ["Você preenche um formulário de 10 minutos", "Manda as fotos dos produtos", "Recebe 10 vídeos narrados em até 5 dias úteis", "Sem reunião"]),
   ("Reels Narrados para sua Loja", capa_produto("09-reels-narrados"))], "REELS", "link com os detalhes e os vídeos de exemplo"),
 ("lanc-calendario", "DATAS 2027", "Quem vende bem na data começa antes",
  [("O que vem no calendário", ["32 datas para moda e calçados", "Quando começar a preparar cada uma", "Kits e ofertas sem furar 2,5x", "Ideias de posts e Reels"]),
   ("Calendário Comercial 2027", capa_produto("10-calendario-2027"))], "CALENDARIO", "link do Calendário Comercial 2027"),
 ("lanc-conteudo", "INSTAGRAM DA LOJA", "Instagram da loja parado de novo?",
  [("Todo mês, pronto", ["20 posts editáveis no Canva", "8 roteiros de Reels", "15 ideias de Stories", "Legendas prontas"]),
   ("Conteúdo do Mês", capa_produto("11-conteudo-do-mes"))], "CONTEUDO", "link da assinatura Conteúdo do Mês"),
]
for tid, kick, gancho, slides, palavra, produto in N:
    arq = [f"{OUT}/{tid}_1.jpg"]; capa(arq[0], kick, gancho)
    for k, (tt, cont) in enumerate(slides, start=2):
        p = f"{OUT}/{tid}_{k}.jpg"; (slide_txt(p, tt, cont) if isinstance(cont, list) else slide_img(p, tt, cont)); arq.append(p)
    p = f"{OUT}/{tid}_{len(arq) + 1}.jpg"; cta(p, palavra, produto); arq.append(p)
    print(tid, "|".join(os.path.relpath(a, BASE).replace(os.sep, "/") for a in arq))
