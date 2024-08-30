import re
from threading import Thread
from app.api.prepdoclib.clean_symbols import CleanSymbolsProcessor

texto = """
## Comunicado: CCI - 1.081/2024 - CCS Brasília/DF, 8 de agosto de 2024.

SICOOB Carta-Circular
de Instrução/Funcionalidade &

CCI - 1.081/2024 - CCS Brasília/DF, 8 de agosto de 2024.


Às entidades do Sicoob.


CCI complementar, referente às evoluções na funcionalidade Reavaliação Garantias do 
módulo Condução de Crédito da Plataforma de Crédito do Sisbr 2.0, em 9/8/2024.


Senhores(as).


1. Em complemento às CClIs - 007/2023, 129/2023, 522/2023, 1.015/2023 e 1.598/2023 -
CCS, de 3/1/2023, 27/1/2023, 24/4/2023, 17/08/2023 e 14/12/2023 respectivamente.

informamos a evolução da funcionalidade Reavaliação Garantias, disponível na
Plataforma de Crédito do Sisbr 2.0, em 9/8/2024, conforme anexo desta CCI.


2. Na data em que a reavaliação está agendada, o sistema verificará, de forma
automática, na Plataforma de Atendimento (Cadastro de Pessoas do Sicoob —
Capes), se a data de avaliação do bem é inferior a 12 (doze) meses da data do agendamento. Caso a última avaliação tenha sido realizada dentro desse novo intervalo de 12 (doze) meses, o sistema procederá com a atualização da data da
última avaliação e do valor da garantia, conforme avaliação mais recente informada
no Capes.


Atenciosamente.

Edson Rodrigues Lisboa Júnior Paulo Antônio Neto Ribeiro Sistemas de Informação | Operações e Produtos de Crédito Superintendente Superintendente Evolutiva negocial
STI: 77127 HRESTRITAÉ
SICOOB Carta-Circular
de Instrução/Funcionalidade &
Anexo Funcionalidade: Reavaliação Garantias 1. Verificar, deforma automática, na data em que a reavaliação está agendada, se a data
de avaliação do bem é inferior a 12 (doze) meses da data do agendamento.

2. Assituações descritas no relatório de Reavaliação de Garantias serão atualizadas da
seguinte forma:
© a) Reavaliação Realizada: garantia que teve a data de avaliação atualizada na
Plataforma de Atendimento (Capes) em até 12 (doze) meses anteriores à data do Objetivo agendamento da reavaliação;
b) Pendente de Reavaliação: garantia que não foi reavaliada na Plataforma de Atendimento (Capes) em até 12 (doze) meses anteriores à data do agendamento da reavaliação.

ENEA i 1, . 1, : ”
LUL—.I Sisbr 2.0 — Plataforma de Crédito — Condução de Crédito — Garantia — Relatórios —
Reavaliação Garantias.

Caminho E A funcionalidade estará disponível para o usuário que possui, pelo menos, um dos seguintes perfis de acesso:
Perfil de acesso Consultas Gerenciais; Controle Interno | e Il; Crédito |, Il, Ill, 1V e V; Fiscalização Crédito |;
Retaguarda VII.

Informações relacionadas à Matriz de Acesso do Centro Cooperativo Sicoob (CCS)
estão disponíveis para consulta no Portal de Serviços do CCS (Base de Conhecimento).

ao informar o código de identificação IC 9118 no campo de pesquisa.

Para as cooperativas que não utilizam a Matriz de Acesso, a atribuição das permissões deverá ser realizada de forma descentralizada aos gestores de acesso, por intermédio da cooperativa central ou singular.

Evolutiva negocial
STI: 77127 HRESTRITAH
SICOOB Carta-Circular
de Instrução/Funcionalidade &
ª Instruções para o usuário Disponíveis para consulta no Portal de Serviços do CCS (Base de Conhecimento), a
partir de 9/8/2024, ao informar os seguintes códigos de identificação no campo de pesquisa:
Código Descrição IC 22180 Reavaliação de Bens Móveis e Imóveis Vinculados em Garantia
IC 22173 Reavaliação de Garantias - Condução de Crédito s/8x — Suporteàs cooperativas 3——'3 Eventuais pedidos de esclarecimentos deverão ser direcionados para a Central de Atendimento à Cooperativa, no número (61) 3771-6600, opção 3, item 1 (para crédito PF/PJ); opção 3, item 3 (para crédito rural); ou por meio de abertura de chamado no Portal de Serviços do CCS, utilizando as seguintes categorizações:
a)  Atendimento à Cooperativa — Crédito Geral (PF/PJ) — Garantias —
Empréstimo — Relatórios/Consultas Garantia — Empréstimo;
b)  Atendimento à Cooperativa — Crédito Agronegócio — Garantia — Crédito Rural — Relatórios/Consultas — Crédito Rural.

Evolutiva negocial
STI: 77127 HRESTRITAH

## Comunicado: CCI — 1.010/2024 - CCS Brasília/DF, 31 de julho de 2024.

SICOOB Carta-Circular
de Instrução &

CCI — 1.010/2024 - CCS Brasília/DF, 31 de julho de 2024.


Às entidades do Sicoob.


Evolução da funcionalidade Multicálculo Automóvel no Sistema Integrado para Gestão e 
Aquisição de Seguros do Sicoob (SicoobSigas) do Sisbr 3.0, referente às mudanças na

integração das seguradoras Porto e Azul.


Senhores(as).


1. Com as mudanças na integração das seguradoras Porto e Azul, informamos a
evolução da funcionalidade Multicálculo Automóvel no SicoobSigas do Sisbr 3.0.

realizada em 24/7/2024, contemplando as seguintes alterações nas companhias:

a) apartirde24/7/2024, os cálculos realizados não serão salvos. Após essa data.

será necessário criar uma simulação para calcular ou contratar seguros;

b) nas renovações de seguros com vigência a partir de 23/8/2024, será
apresentado um pacote fechado de condição exclusiva de cada seguradora.

Não será válido o recálculo ou ajustes de coberturas;

c)  paraoscasosem que há uma recusa no produto tradicional, disponibilizamos uma oferta alternativa, denominada Cotação para Todos, com condições adequadas para cada cooperado. Nessa oferta, serão apresentadas as coberturas de Incêndio, Roubo e Furto, Compreensiva Fipe de até 80% (oitenta
por cento) ou RCF. Não será válido recálculo ou ajustes de coberturas;

d) o Desconto Cota Prêmio está disponível na opção Condições Especiais.

conforme o saldo acumulado da corretora. O desconto não é aplicável para o pacote de renovação;

e)  quando exigida a vistoria prévia pela seguradora, será apresentada na tela de contratação a seguinte mensagem, com o link para baixar o aplicativo de 
HRESTRITA
SICOOB Carta-Circular
de Instrução &
vistoria da seguradora:
Contratação realizada com sucesso! Proposta gerada na seguradora. Atenção.

existem pendências na segurada. Para a contratação do seu seguro é preciso efetuar a vistoria prévia digital. Baixe o App da vistoria através do link.


11 O usuário poderá acessar a funcionalidade Multicálculo Automóvel, utilizando o seguinte caminho: Sisbr 2.0 — Sigas (Direcionamento para o Sisbr 3.0) — Nome ou
CPF/CNPJ — Novo Negócio — Portal de Vendas — Automóvel Multicálculo.


É As funcionalidades estão disponíveis para o usuário que possui, pelo menos, um dos seguintes perfis de acesso:
Perfil de acesso Atendimento |, II, IIll e IV; Crédito |, II, IlI, IV e V; Retaguarda |, II, N e IV.

Informações relacionadas à Matriz de Acesso do Centro Cooperativo Sicoob (CCS)
estão disponíveis para consulta no Portal de Serviços do CCS (Base de Conhecimento).

ao informar o código de identificação IC 9118 no campo de pesquisa.

Para as cooperativas que não utilizam a Matriz de Acesso, a atribuição das permissões deverá ser realizada de forma descentralizada aos gestores de acesso, por intermédio da cooperativa central ou singular.

HRESTRITA
SICOOB Carta-Circular
de Instrução &
/gx Suporte às cooperativas gvg Eventuais pedidos de esclarecimentos deverão ser direcionados para o Portal de Serviços do CCS, por meio de abertura de chamado, utilizando a seguinte categorização: Atendimento à Cooperativa — Seguros — Seguro Automóvel —
Dúvidas Negociais do Produto — Seguro Automóvel.

Atenciosamente.

Edson Rodrigues Lisboa Júnior Henrique Neves Jersey
Sistemas de Informação | Comercial de Seguros Gerais Superintendente Gerente HRESTRITA


"""

texto2 = """
CCI - 1.888/2020 - CCS Brasília/DF, 23 de novembro de 2023.
Às entidades do Sicoob.
Assunto: Remanejamento de valores de benefícios do cartão Coopcerto
(alimentação e refeição) pela atendente digital Alice, por meio do 
WhatsApp.
Senhores(as),
1. Dando continuidade às melhorias e entregas direcionadas para as entidades CCI - 4321 do 
Sicoob, informamos que, a partir de 1º/12/2023, os empregados das cooperativas 
centrais, das cooperativas singulares e do Centro Cooperativo Sicoob (CCS)
poderão requisitar de maneira automática o remanejamento dos valores de 
benefícios CCI - 222/2005 dos cartões Coopcerto, nas modalidades vale alimentação e vale 
refeição, tornando a ação de mudança mais ágil e descomplicada.
"""

"""
def extrair_numeros_comunicados(text: str) -> None:
    result = re.findall('[CCI - ]+[ |0-9|.|-]{1,9}', text)
    print (result)


if __name__ == "__main__":
    t1 = Thread(target=extrair_numeros_comunicados, args=(texto,))
    t2 = Thread(target=extrair_numeros_comunicados, args=(texto2,))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("Done!") """
    
if __name__ == "__main__":
    finais = ['a\r\n','b\r\n','c\r\n','d\r\n','e\r\n','f\r\n','g\r\n','h\r\n','i\r\n','j\r\n','l\r\n','m\r\n','n\r\n', 'o\s\r\n','p\r\n','q\r\n','r\r\n','s\r\n','v\r\n','u\r\n','x\r\n','z\r\n']
    novo_texto = ''
    #for final in finais:
    #    print(final) —
    #    novo_texto = texto.replace(final, ' ')
    texto = texto.replace(' \n', '\n').replace('— \n', '— ').replace('—\n', '— ').replace('- \n', '- ').replace('-\n', '- ').replace(') \n', ') ').replace(')\n', ') ').replace('o \n', 'o ').replace('o\n', 'o ').replace('s \n', 's ').replace('s\n', 's ').replace('e \n', 's ').replace('e\n', 'e ').replace('a \n', 'a ').replace('a\n', 'a ').replace('r \n', 'r ').replace('r\n', 'r ').replace('á \n', 'á ').replace('á\n', 'á ').replace('HRESTRITA', '')
    cleaner = CleanSymbolsProcessor()
    print(cleaner.process_line(texto))
    
    
    import pytesseract
import cv2

img = cv2.imread('image.jpg')

# Detect text regions
rects = detector(img)

# Extract text from regions
text = ""
for rect in rects:
   x, y, w, h = rect
   text += pytesseract.image_to_string(img[y:y+h, x:x+w])