# -*- coding: utf-8 -*-
"""NewsRecommenderAssignment.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1vJ0J-8zzh0ONtWBELmEuuSzIIvt9eJFD

Libraries
"""

import pandas as pd
import numpy as np
from numpy import linalg
import matplotlib.pyplot as plt

from scipy.optimize import nnls

#for lemmatization
import nltk
nltk.download("wordnet")
nltk.download('stopwords')
#to remove stop words
from nltk.corpus import stopwords

#for tf-idf
from sklearn.feature_extraction.text import TfidfVectorizer

#cosine similarity
from sklearn.metrics.pairwise import cosine_similarity

#gaussian mixture
from sklearn.mixture import GaussianMixture

from sklearn.decomposition import TruncatedSVD# TruncatedSVD
from sklearn.decomposition import LatentDirichletAllocation

"""# **Importing the collected data**"""

df_1 = pd.read_csv("agrima_news_data.csv")
df_2 = pd.read_csv("sarvesh_news_data.csv")
df_3 = pd.read_csv("satender_news_data.csv")
df_4 = pd.read_csv("vishal_news_data.csv")

"""# **Preprocessing the csv files.**"""

del df_1['Unnamed: 0']
del df_2['index']
del df_2['Unnamed: 0']
df_2.rename(columns = {'content':'Content'}, inplace = True)
del df_3['Unnamed: 0']
del df_3['Title']
del df_4['Unnamed: 0']

"""**Remove capitalization, numbers, stop words, non-english characters, drop empty rows and duplicates.**"""

news_corpus = pd.concat([df_1,df_2,df_3,df_4],ignore_index=True)
news_corpus = news_corpus.dropna() #dropping NaN
news_corpus = news_corpus[news_corpus.Content != ''] #dropping empty rows
news_corpus = news_corpus.drop_duplicates()
news_corpus["Content"] = news_corpus['Content'].str.replace('[^\w\s]',' ')
news_corpus = news_corpus[news_corpus['Content'].map(lambda x: x.isascii())] #remove non-english #find a better way
news_corpus['Content'] = news_corpus['Content'].str.lower() #convert to lowercase
news_corpus.replace('\d+', '', regex=True, inplace=True) #remove numbers

stop_words = stopwords.words('english')
stop_words.extend(['span','class','spacing','href','html','http','title','said','that'])
news_corpus['Content'] = news_corpus['Content'].apply(lambda x: ' '.join([w for w in x.split() if len(w)>3]))
news_corpus = news_corpus.apply(lambda x: [item for item in x if item not in stop_words])

"""Storing a second news corpus to show the original news without preprocessing."""

news_corpus_org = pd.concat([df_1,df_2,df_3,df_4],ignore_index=True)
news_corpus_org = news_corpus_org.dropna() #dropping NaN
news_corpus_org = news_corpus_org[news_corpus_org.Content != ''] #dropping empty rows
news_corpus_org = news_corpus_org.drop_duplicates()
news_corpus_org["Content"] = news_corpus_org['Content'].str.replace('[^\w\s]',' ')
news_corpus_org = news_corpus_org[news_corpus_org['Content'].map(lambda x: x.isascii())]

news_corpus_org_temp = pd.concat([df_1,df_2,df_3,df_4],ignore_index=True)
news_corpus_org_temp = news_corpus_org_temp.dropna() #dropping NaN
news_corpus_org_temp = news_corpus_org_temp[news_corpus_org_temp.Content != ''] #dropping empty rows
news_corpus_org_temp = news_corpus_org_temp.drop_duplicates()

org_news_dict = news_corpus_org_temp.Content.to_dict()
del news_corpus_org['Content']
news_corpus_org['Content'] = news_corpus_org.index
news_corpus_org = news_corpus_org.replace(org_news_dict)
news_corpus_org = news_corpus_org.reset_index(drop=True)

news_corpus_org

"""**Lemmatization**"""

w_tokenizer = nltk.tokenize.WhitespaceTokenizer()
lemmatizer = nltk.stem.WordNetLemmatizer()
def lemmatize_text(text):
    return [lemmatizer.lemmatize(w) for w in w_tokenizer.tokenize(text)]

news_corpus['Content'] = news_corpus.Content.apply(lemmatize_text)
news_corpus['Content'] = news_corpus['Content'].apply(', '.join) #convert list of words to a sentence
news_corpus.replace(',', '', regex=True, inplace=True) # remove commas
news_corpus = news_corpus.reset_index(drop=True)
news_corpus

"""# TF-IDF"""

vectorizer = TfidfVectorizer()
vectors = vectorizer.fit_transform(news_corpus.Content)
feature_names = vectorizer.get_feature_names()
dense = vectors.todense()
#denselist = dense.tolist() #very expensive
df_vecs = pd.DataFrame(dense, columns=feature_names)
df_vecs

"""# **LSA : Latent Semantic Analysis**"""

sv_dec = TruncatedSVD(n_components = 50)  # components(no. of latent factors) < n ; n : no. of docs.
ls_analysis = sv_dec.fit_transform(vectors.T)

sv_dec.singular_values_ # eigenvalues for svd (in decreasing order)

variance =  sv_dec.singular_values_/sum(sv_dec.singular_values_) # checking the variance captured by eigenvalues
variance

sv_dec = TruncatedSVD(n_components = 25) # components with accepted variance
las = sv_dec.fit_transform(vectors)

#print(las,las.shape)

"""Topic - Document matrix"""

# Representation of each doc in terms of latent topics after dimensionality reduction
col = []
for i in range(las.shape[1]):
    col.append("topic_{}".format(i)) 

topic_df = pd.DataFrame(las, columns = col)

topic_df["Docs"] = news_corpus.Content

l = ["Docs"]
for i in col:
    l.append(i)

#display(topic_df[l])

"""**Topics and terms list**"""

Sigma = sv_dec.singular_values_ 
V_transpose = sv_dec.components_.T
terms = vectorizer.get_feature_names()

for index, component in enumerate(sv_dec.components_):
    zipped = zip(terms, component)
    top_terms_key=sorted(zipped, key = lambda t: t[1], reverse=True)[:10]
    top_terms_list=list(dict(top_terms_key).keys())
    print("Topic "+str(index)+": ",top_terms_list)
del Sigma,V_transpose,terms,zipped,top_terms_key

"""# **LDA : Latent Dirichlet Allocation**"""

#lda
'''
lda = LatentDirichletAllocation(n_components=25)
lda_matrix = lda.fit_transform(df_vecs)
lda_topics = lda.fit(df_vecs)
for idx, topic in enumerate(lda.components_):
        print ("Topic ", idx, " ".join(feature_names[i] for i in topic.argsort()[:-10 - 1:-1]))

def plot_top_words(model, feature_names, n_top_words, title):
    fig, axes = plt.subplots(2, 5, figsize=(30, 15), sharex=True)
    axes = axes.flatten()
    for topic_idx, topic in enumerate(model.components_):
        top_features_ind = topic.argsort()[:-n_top_words - 1:-1]
        top_features = [feature_names[i] for i in top_features_ind]
        weights = topic[top_features_ind]

        ax = axes[topic_idx]
        ax.barh(top_features, weights, height=0.7)
        ax.set_title(f'Topic {topic_idx +1}',
                     fontdict={'fontsize': 30})
        ax.invert_yaxis()
        ax.tick_params(axis='both', which='major', labelsize=20)
        for i in 'top right left'.split():
            ax.spines[i].set_visible(False)
        fig.suptitle(title, fontsize=40)

    plt.subplots_adjust(top=0.90, bottom=0.05, wspace=0.90, hspace=0.3)
    plt.show()

#plot_top_words(lda, feature_names, 10, "t")

col = []
for i in range(lda_matrix.shape[1]):
    col.append("topic_{}".format(i)) 

topic_df_2 = pd.DataFrame(lda_matrix, columns = col)

topic_df_2["Docs"] = news_corpus.Content

l = ["Docs"]
for i in col:
    l.append(i)
'''
#display(topic_df_2[l])

"""**Cosine Similarity**"""

cos_sim = pd.DataFrame(cosine_similarity(topic_df.iloc[:, :-1]))
cos_sim

"""# **Creating Users and initial ratings**

**Generating Users**
"""

#fitting GMM to column "topic_i"

num_cols_topic_df = topic_df.shape[1]-1
gm = []

for i in range(num_cols_topic_df):
  gm.append(GaussianMixture(n_components=10).fit(topic_df.iloc[:, [i]]))

#generating gmm based topic values for each topic for 50 users
#24 x 50 matrix

Users = []

for i in range(50):
  temp = []
  for i in range(num_cols_topic_df):
    temp.append(gm[i].sample(1)[0][0][0])
  Users.append(temp)
Users=np.array(Users)
Users.T
l2norm = np.sqrt((Users * Users).sum(axis=1))
Users = pd.DataFrame(Users/l2norm.reshape(50,1))

#run the above cell before running this twice
slc = list(range(topic_df.shape[1]))
slc.remove(25)
temp_topic_df = topic_df.iloc[:, slc]
Users_temp = Users.T.set_index(temp_topic_df.T.index)

result = temp_topic_df.dot(Users_temp);
#result.T

"""**Generating User ratings** 



"""

rank_matrix = result.rank().T/4593*10
rank_matrix = rank_matrix.round(0).astype(int)
rank_matrix.columns =np.linspace(0,4593,4594).astype(int)

#not every reader reads all news
#remove random elements from the rank matrix
for i in range(4594):
  random_entries = np.random.randint(0,50,25)
  rank_matrix.loc[random_entries,i] = "No rating"
rank_matrix = rank_matrix.apply(pd.to_numeric, errors='coerce')
rank_matrix

"""# **Content based recommender function**"""

def content_recommender(rank_matrix,cos_sim):
  
  #find top 5 ratings
  top_five = rank_matrix.apply(lambda s, n: pd.Series(s.nlargest(n).index), axis=1, n=5)

  #best two similar docs for every doc
  best_two = cos_sim.apply(lambda s, n: pd.Series(s.nlargest(n).index), axis=1, n=3)
  best_two.columns =['0', '1','2']
  del best_two['0']
  best_two['combined']= best_two.values.tolist()
  best_two
  best_two_dict_1 = best_two['1'].to_dict()
  best_two_dict_2 = best_two['2'].to_dict()

  selected_docs_1 = top_five.replace(best_two_dict_1)
  selected_docs_2 = top_five.replace(best_two_dict_2)
  selected_docs_with_ID = pd.concat([selected_docs_1,selected_docs_2],axis=1,ignore_index=True)

  #replace value by the actual news
  doc_dict = news_corpus_org.Content.to_dict()

  selected_docs = selected_docs_with_ID.replace(doc_dict)
  return selected_docs, selected_docs_with_ID

"""# **Top 10 news : Content based recommender.**"""

#selected_docs_content,selected_docs_content_with_ID = content_recommender(rank_matrix,cos_sim)
#selected_docs_content

"""# **Collaborative recommender function: Predict missing ratings using Matrix factorization**"""

#collaborative recommender function

def collaborative_recommender(rank_matrix,num_iter,news_corpus):
  A = np.array(rank_matrix)
  M = A.shape[0]
  N = A.shape[1]
  A_df = pd.DataFrame(A)
  K = 25
  W = np.abs(np.random.uniform(low=0, high=1, size=(M, K)))
  H = np.abs(np.random.uniform(low=0, high=1, size=(K, N)))
  W = np.divide(W, K*W.max())
  H = np.divide(H, K*H.max())

  #cost func
  def cost(A, W, H):
    mask = pd.DataFrame(A).notnull().values
    WH = np.dot(W, H)
    WH_mask = WH[mask]
    A_mask = A[mask]
    A_WH_mask = A_mask-WH_mask
    return linalg.norm(A_WH_mask, 2)
  
  #optimization loop
  num_display_cost = max(int(num_iter/10), 1)

  for i in range(num_iter):
      if i%2 ==0:
          # Learn H, given A and W
          for j in range(N):
              mask_rows = pd.Series(A[:,j]).notnull()
              H[:,j] = nnls(W[mask_rows], A[:,j][mask_rows])[0]
      else:
          for j in range(M):
              mask_rows = pd.Series(A[j,:]).notnull()
              W[j,:] = nnls(H.transpose()[mask_rows], A[j,:][mask_rows])[0]
              
      WH = np.dot(W, H)
      c = cost(A, W, H)
      #if i%num_display_cost==0:
      print(i, c)
  W = pd.DataFrame(W)
  H = pd.DataFrame(H)
  A = W.dot(H)
  
  #new rank matrix
  A = A.round(0).astype(int)
  A = np.clip(A,1,10)
  #finding the top 10 documents
  selected_docs_with_ID = A.apply(lambda s, n: pd.Series(s.nlargest(n).index), axis=1, n=10)
  selected_docs_with_ID.columns =['1', '2', '3', '4', '5','6','7','8','9','10']
  doc_dict = news_corpus_org.Content.to_dict()
  selected_docs = selected_docs_with_ID.replace(doc_dict)
  return selected_docs, selected_docs_with_ID

"""# **Top 10 news : Collaborative recommender.**"""

num_iter = 10
#selected_docs_collab,selected_docs_collab_with_ID = collaborative_recommender(rank_matrix,num_iter,news_corpus)
#selected_docs_collab

"""# **Hydrid recommender**"""

def hybrid(collaborative_recommender,content_recommender,rank_matrix,cos_sim,news_corpus):
  selected_docs_collab,selected_docs_collab_with_ID = collaborative_recommender(rank_matrix,num_iter,news_corpus)
  selected_docs_content,selected_docs_content_with_ID = content_recommender(rank_matrix,cos_sim)
  
  selected_docs_collab.reset_index(drop=True, inplace=True)
  selected_docs_content.reset_index(drop=True, inplace=True)
  
  selected_docs_collab_with_ID.reset_index(drop=True, inplace=True)
  selected_docs_content_with_ID.reset_index(drop=True, inplace=True)
  
  selected_docs_final = pd.concat([selected_docs_content.iloc[:,[0,1,2,3,4]],selected_docs_collab.iloc[:,[5,6,7,8,9]]],axis=1)
  selected_docs_final_with_ID = pd.concat([selected_docs_content_with_ID.iloc[:,[0,1,2,3,4]],selected_docs_collab_with_ID.iloc[:,[5,6,7,8,9]]],axis=1)
  
  return selected_docs_final,selected_docs_final_with_ID

"""# **Top 10 news : Hybrid recommender.**"""

selected_docs_final,selected_docs_final_with_ID = hybrid(collaborative_recommender,content_recommender,rank_matrix,cos_sim,news_corpus)
selected_docs_final

"""# **User Profile Updater**

Implemented in the flask app.

# **Implement ALS based matrix factorization instead of NNLS**
"""

'''from pyspark.ml.recommendation import ALS 
from pyspark.sql.types import FloatType
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql.functions import col

X_train, X_test = rank_matrix.randomSplit([0.6, 0.4])'''

'''als = mlALS(rank=5, maxIter=10, seed=0)
model = als.fit(rank_matrix)'''
