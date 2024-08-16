import re
from threading import Thread

texto = """
CCI - 1.477/2023 - CCS Brasília/DF, 23 de novembro de 2023.
Às entidades do Sicoob.
Assunto: Remanejamento de valores de benefícios do cartão Coopcerto
(alimentação e refeição) pela atendente digital Alice, por meio do 
WhatsApp.
Senhores(as),
1. Dando continuidade às melhorias e entregas direcionadas para as entidades CCI - 1234 do 
Sicoob, informamos que, a partir de 1º/12/2023, os empregados das cooperativas 
centrais, das cooperativas singulares e do Centro Cooperativo Sicoob (CCS)
poderão requisitar de maneira automática o remanejamento dos valores de 
benefícios CCI - 983/2028 dos cartões Coopcerto, nas modalidades vale alimentação e vale 
refeição, tornando a ação de mudança mais ágil e descomplicada.
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

    print("Done!")