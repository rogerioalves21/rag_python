https://www.youtube.com/watch?v=8OJC21T2SL4

import pandas as pd

df = pd.read_csv(
    "https://raw.githubusercontent.com/mistralai/cookbook/main/data/Symptom2Disease.csv",
    index_col=0,
)

def get_embeddings_by_chunks(data, chunk_size):
    chunks = [data[x : x + chunk_size] for x in range(0, len(data), chunk_size)]
    embeddings_response = [
        client.embeddings.create(model=model, inputs=c) for c in chunks
    ]
    return [d.embedding for e in embeddings_response for d in e.data]

df["embeddings"] = get_embeddings_by_chunks(df["text"].tolist(), 50)
df.head()



import seaborn as sns
from sklearn.manifold import TSNE
import numpy as np

tsne = TSNE(n_components=2, random_state=0).fit_transform(np.array(df['embeddings'].to_list()))
ax = sns.scatterplot(x=tsne[:, 0], y=tsne[:, 1], hue=np.array(df['label'].to_list()))
sns.move_legend(ax, 'upper left', bbox_to_anchor=(1, 1))



import fasttext.util

fasttext.util.download_model('en', if_exists='ignore')  # English
ft = fasttext.load_model('cc.en.300.bin')

df['fasttext_embeddings'] = df['text'].apply(lambda x: ft.get_word_vector(x).tolist())

tsne = TSNE(n_components=2, random_state=0).fit_transform(np.array(df['fasttext_embeddings'].to_list()))
ax = sns.scatterplot(x=tsne[:, 0], y=tsne[:, 1], hue=np.array(df['label'].to_list()))
sns.move_legend(ax, 'upper left', bbox_to_anchor=(1, 1))



from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

# Create a train / test split
train_x, test_x, train_y, test_y = train_test_split(
    df["embeddings"], df["label"], test_size=0.2
)

# Normalize features
scaler = StandardScaler()
train_x = scaler.fit_transform(train_x.to_list())
test_x = scaler.transform(test_x.to_list())

# Train a classifier and compute the test accuracy
# For a real problem, C should be properly cross validated and the confusion matrix analyzed
clf = LogisticRegression(random_state=0, C=1.0, max_iter=500).fit(
    train_x, train_y.to_list()
)
# you can also try the sag algorithm:
# clf = LogisticRegression(random_state=0, C=1.0, max_iter=1000, solver='sag').fit(train_x, train_y)

print(f"Precision: {100*np.mean(clf.predict(test_x) == test_y.to_list()):.2f}%")



# Classify a single example
text = "I've been experiencing frequent headaches and vision problems."
clf.predict([get_text_embedding([text])])






# Create a train / test split
train_x, test_x, train_y, test_y = train_test_split(
    df["fasttext_embeddings"], df["label"], test_size=0.2
)

# Normalize features
scaler = StandardScaler()
train_x = scaler.fit_transform(train_x.to_list())
test_x = scaler.transform(test_x.to_list())

# Train a classifier and compute the test accuracy
# For a real problem, C should be properly cross validated and the confusion matrix analyzed
clf = LogisticRegression(random_state=0, C=1.0, max_iter=500).fit(
    train_x, train_y.to_list()
)
# you can also try the sag algorithm:
# clf = LogisticRegression(random_state=0, C=1.0, max_iter=1000, solver='sag').fit(train_x, train_y)

print(f"Precision: {100*np.mean(clf.predict(test_x) == test_y.to_list()):.2f}%")



from sklearn.cluster import KMeans

model = KMeans(n_clusters=24, max_iter=1000)
model.fit(df['embeddings'].to_list())
df["cluster"] = model.labels_
print(*df[df.cluster==23].text.head(3), sep='\n\n')