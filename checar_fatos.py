import ollama
import warnings
from mattsollamatools import chunker
import numpy as np
from sklearn.neighbors import NearestNeighbors
import nltk


# https://www.youtube.com/watch?v=IjKOw02wOhg

warnings.filterwarnings(
    "ignore", category=FutureWarning, module="transformers.tokenization_utils_base"
)
nltk.download("punkt_tab", quiet=True)

article = dict()

def get_processo_judicial() -> str:
    with open('50059699220248210038.txt', 'r', encoding='utf-8') as f:
        return f.read()

def getContexto() -> str:
    # ler o arquivo texto
    return """
Presente em todo o Brasil, o Sicoob é o maior sistema financeiro cooperativo do país.
Cuidamos das fi nanças e do futuro de mais de 4,6 milhões brasileiros — pessoas físicas e jurídicas.
Temos agências em 1.842 municípios brasileiros, nas 27 unidades da Federação. 

Em 294 deles, somos a única instituição financeira presente para atender a população.

Conectamos pessoas para promover justiça fi nanceira e prosperidade a todos. Somos diferentes dos bancos comerciais. Dinheiro, para nós, é ferramenta de inclusão e desenvolvimento, capaz de melhorar a vida tanto dos nossos correntistas quanto das comunidades onde atuamos.

Por isso, realizamos investimentos consistentes em projetos socioambientalmente sustentáveis, estimulando a economia local e a cultura da cooperação por onde passamos. 

Também somos reconhecidos no mercado financeiro pela efi ciência e confi abilidade dos 
nossos canais digitais. Basta dizer que 78% 
das nossas transações fi nanceiras são realizadas online. Investimos tanto em inovação 
que colecionamos prêmios na área de tecnologia da informação, especialmente nos 
quesitos excelência e segurança dos aplicativos para celular. Aliás, vale destacar: desde 
2018, o mobile se tornou o principal canal de 
relacionamento do Sicoob com os cooperados, na frente de caixas eletrônicos, agências 
e atendimento por telefone. 
Outro diferencial importante: a qualidade do 
atendimento. Nossos cooperados sentem-se 
em casa quando vão à cooperativa. Afi nal, 
além de usuários, são donos do negócio. Por 
isso, fazemos questão de recebê-los com 
o cuidado e o respeito que merecem. Um 
atendimento feito por pessoas que gostam 
de pessoas. Gente como você, que acredita 
ser possível cuidar do bolso sem abrir mão 
de valores.
"""

def knn_search(question_embedding, embeddings, k=5):
    """Performs K-nearest neighbors (KNN) search"""
    X = np.array(
        [item["embedding"] for article in embeddings for item in article["embeddings"]]
    )
    source_texts = [
        item["source"] for article in embeddings for item in article["embeddings"]
    ]

    # Fit a KNN model on the embeddings
    knn = NearestNeighbors(n_neighbors=k, metric="cosine")
    knn.fit(X)

    # Find the indices and distances of the k-nearest neighbors.
    _, indices = knn.kneighbors(question_embedding, n_neighbors=k)

    # Get the indices and source texts of the best matches
    best_matches = [(indices[0][i], source_texts[indices[0][i]]) for i in range(k)]

    return best_matches

def check(document, claim):
    """Checks if the claim is supported by the document by calling bespoke-minicheck.

    Returns Yes/yes if the claim is supported by the document, No/no otherwise.
    Support for logits will be added in the future.

    bespoke-minicheck's system prompt is defined as:
      'Determine whether the provided claim is consistent with the corresponding
      document. Consistency in this context implies that all information presented in the claim
      is substantiated by the document. If not, it should be considered inconsistent. Please
      assess the claim's consistency with the document by responding with either "Yes" or "No".'

    bespoke-minicheck's user prompt is defined as:
      "Document: {document}\nClaim: {claim}"
    """
    prompt = f"Document: {document}\nClaim: {claim}"
    response = ollama.generate(
        model="bespoke-minicheck:7b-q2_K", prompt=prompt, options={"num_predict": 2, "temperature": 0.0}
    )
    return response["response"].strip()

if __name__ == "__main__":
    allEmbeddings = []
    article = {}
    article["embeddings"] = []
    text = get_processo_judicial()
    chunks = chunker(text, language='portuguese')

    # Embed (batch) chunks using ollama
    embeddings = ollama.embed(model="nomic-embed-text", input=chunks)["embeddings"]

    for chunk, embedding in zip(chunks, embeddings):
        item = {}
        item["source"] = chunk
        item["embedding"] = embedding
        item["sourcelength"] = len(chunk)
        article["embeddings"].append(item)

    allEmbeddings.append(article)

    print("\nLoaded, chunked, and embedded text.\n")

    while True:
        # Input a question from the user
        # For example, "Who is the chief research officer?"
        question = input("Enter your question or type quit: ")

        if question.lower() == "quit":
            break

        # Embed the user's question using ollama.embed
        question_embedding = ollama.embed(model="nomic-embed-text", input=question)[
            "embeddings"
        ]

        # Perform KNN search to find the best matches (indices and source text)
        best_matches = knn_search(question_embedding, allEmbeddings, k=4)

        sourcetext = "\n\n".join([source_text for (_, source_text) in best_matches])

        print(f"\nRetrieved chunks: \n{sourcetext}\n")

        # Give the retreived chunks and question to the chat model
        system_prompt = f"Only use the following information to answer the question. Do not use anything else: {sourcetext}"

        ollama_response = ollama.generate(
            model="qwen2.5:3b",
            prompt=question,
            system=system_prompt,
            options={"stream": False},
        )

        answer = ollama_response["response"]
        print(f"LLM Answer:\n{answer}\n")

        # Check each sentence in the response for grounded factuality
        if answer:
            for claim in nltk.sent_tokenize(answer):
                print(f"LLM Claim: {claim}")
                print(
                    f"Is this claim supported by the context according to bespoke-minicheck? {check(sourcetext, claim)}\n"
                )
        print("proxima pergunta!\n")