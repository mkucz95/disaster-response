import sys
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
import nltk
from sklearn.externals import joblib

nltk.download(['punkt', 'wordnet', 'averaged_perceptron_tagger'])

import re
import numpy as np
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from sklearn.metrics import classification_report
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.multioutput import MultiOutputClassifier

def load_data(database_filepath):
    engine = create_engine('sqlite:///{}'.format(database_filepath))
    conn = sqlite3.connect(database_filepath)
    df = pd.read_sql("SELECT * FROM {}".format(database_filepath), con=conn)
    X= df.messages.values
    Y = df.iloc[:,4:]
    return X, Y

def tokenize(text):
    tokens = word_tokenize(text) #split each message into individual words
    lemmatizer = WordNetLemmatizer()
    clean_tokens=[]
    for token in tokens:
        #clean each token from whitespace and punctuation, and conver to
        #root of word ie walking->walk
        clean_token = lemmatizer.lemmatize(token).lower().strip()
        clean_tokens.append(clean_token)
    return clean_tokens

def build_model():
    #get the matrix of counts for each word in messages
    #do tfidf transformation which shows occurence in realtion to number of documents
    #perform randomforest on multioutpit classifier
    pipeline = Pipeline([
        ('features', FeatureUnion([

            ('textpipeline', Pipeline([
                ('vect', CountVectorizer(tokenizer=tokenize, ngram_range=(1,2))),
                ('tfidf', TfidfTransformer())
            ])),

            ('mesg_len', MessageLengthExtractor()),
            ('noun_start', StartingNounExtractor()),
            ('contains_num', NumericalExtractor())
        ])),
        ('clf', MultiOutputClassifier(AdaBoostClassifier()))
    ])
    return pipeline

def evaluate_model(model, X_test, Y_test, category_names):
    predictions = pd.DataFrame(model.predict(X_test), columns = y_test.columns)
    for col in category_names:
        print(col)
        print(classification_report(Y_test[col], predictions[col]))
        
def save_model(model, model_filepath):
    joblib.dump(model, model_filepath);

def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()